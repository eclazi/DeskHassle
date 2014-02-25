'''
Hassle.py

joss@jossgray.net

'''

import argparse
import json
import smtplib

import requests


def main(desk_username, desk_password, desk_company, email_server, email_username, email_pwd):
    server = smtplib.SMTP(email_server, 587)
    server.ehlo()
    server.starttls()
    server.login(email_username, email_pwd)

    def getEntries(url):
        r = requests.get(url, auth=(desk_username, desk_password))
        data = json.loads(r.text)
        entries = data['_embedded']['entries']
        return entries

    cases = getEntries('https://' + desk_company + '.desk.com/api/v2/cases/search?status=open,pending')
    users = getEntries('https://' + desk_company + '.desk.com/api/v2/users')

    opencases = {}

    for user in users:
        opencases[user['_links']['self']['href']] = {'email': user['email'], 'name': user['name'], 'cases': []}

    for case in cases:
        if case['_links']['assigned_user'] != None:
            subject = case['subject']
            opencases[case['_links']['assigned_user']['href']]['cases'].append(subject)

    for p in opencases:
        name = opencases[p]['name']
        email = opencases[p]['email']
        cases = opencases[p]['cases']
        nCases = len(cases)

        if nCases > 0:
            text = '%s \n\nYou have %d uresolved cases on desk.com.\n\n' % (name, nCases)
            for case in cases:
                text += '%s\n' % case

            text += '\nHurry up\n'
            header = 'From: %s\nTo: %s\nSubject: %s\n' % (email_username, email, 'Open Cases on Desk.com')
            text = header + text
            try:
                server.sendmail(email_username, email, text)
                print(text)
                print('Sent email')
            except:
                print('failed to send')


def create_argument_parser():
    parser = argparse.ArgumentParser(description='Hassle users on desk.com to close their tickets')
    parser.add_argument('desk_username')
    parser.add_argument('desk_pwd')
    parser.add_argument('desk_company')
    parser.add_argument('email_server')
    parser.add_argument('email_username')
    parser.add_argument('email_pwd')
    return parser


if __name__ == '__main__':
    parser = create_argument_parser()
    args = parser.parse_args()
    main(args.desk_username,
         args.desk_pwd,
         args.desk_company,
         args.email_server,
         args.email_username,
         args.email_pwd)