'''
Hassle.py

joss@jossgray.net

'''

import argparse
import smtplib

import requests


class DeskError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message

    def __str__(self):
        return '%s: %d, %s' % (self.__class__.__name__, self.status_code, self.message)

    def __repr__(self):
        return '%s(%d, %s)' % (self.__class__.__name__, self.status_code, self.message)


class DeskApi(object):
    def __init__(self, desk_username, desk_password, desk_company):
        self.desk_username = desk_username
        self.desk_password = desk_password
        self.desk_company = desk_company

    @property
    def desk_url(self):
        return 'https://%s.desk.com' % self.desk_company

    def request_url(self, path):
        return '%s%s' % (self.desk_url, path)

    def make_request(self, path):
        r = requests.get(self.request_url(path), auth=(self.desk_username, self.desk_password))
        if r.status_code != 200:
            raise DeskError(r.status_code, r.json().get('message', 'Unknown'))
        return r

    def multi_page_request(self, url):
        while url:
            r = self.make_request(url).json()

            # get the next page url
            if r.get('_links') and r['_links'].get('next'):
                url = r['_links']['next']['href']
            else:
                url = False
            yield r

    def cases(self, user='', filter=['open', 'pending', 'resolved', 'new', 'closed']):
        url = '/api/v2/cases/search?status=%s&assigned_user=%s' % (','.join(filter), user.replace(' ', '+'))
        for page in self.multi_page_request(url):
            for case in page['_embedded']['entries']:
                yield case

    def users(self):
        url = '/api/v2/users'
        for page in self.multi_page_request(url):
            for user in page['_embedded']['entries']:
                yield user


class EmailContentGenerator(object):
    email_text = '''
You have %s unresolved cases on desk.com.

%s

Hurry Up.
'''

    def __init__(self, desk_username, desk_pwd, desk_company):
        self.desk_username = desk_username
        self.desk_pwd = desk_pwd
        self.desk_company = desk_company

        self.api = DeskApi(self.desk_username, self.desk_pwd, self.desk_company)

    def create_cases_text(self, cases):
        return '\n'.join([case['subject'] for case in cases])

    def emails_body(self):
        for desk_user in self.api.users():
            cases = [case for case in self.api.cases(user=desk_user['name'], filter=['open', 'pending'])]
            if len(cases) > 0:
                yield desk_user['email'], self.email_text % (len(cases), self.create_cases_text(cases))


def create_argument_parser():
    parser = argparse.ArgumentParser(description='Hassle users on desk.com to close their tickets')
    parser.add_argument('desk_username')
    parser.add_argument('desk_pwd')
    parser.add_argument('desk_company')
    parser.add_argument('email_server')
    parser.add_argument('email_username')
    parser.add_argument('email_pwd')
    parser.add_argument('--email_port', type=int, default=587)
    return parser


if __name__ == '__main__':
    parser = create_argument_parser()
    args = parser.parse_args()

    email_gen = EmailContentGenerator(args.desk_username, args.desk_pwd, args.desk_company)

    # setup email client
    email = smtplib.SMTP(args.email_server, args.email_port)
    email.ehlo()
    email.starttls()
    email.login(args.email_username, args.email_pwd)

    for user_email, body in email_gen.emails_body():
        header = 'From: %s\nTo: %s\nSubject: %s\n' % (args.email_username, user_email, 'Open Cases on Desk.com')
        email_text = header + body

        try:
            email.sendmail(args.email_username, user_email, email_text)
            print(email_text)
            print('Sent email')
        except:
            print('failed to send')

