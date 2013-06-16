'''
Hassle.py

joss@jossgray.net

'''

import requests
import json
import smtplib

user = 'deskusername'
password = 'deskpwd'
company = 'company'

email_server = 'emailserver'
email_user = 'emailusername'
email_pwd = 'emailpwd'

def main():

	server = smtplib.SMTP(email_server, 587)
	server.ehlo()
	server.starttls()
	server.login(email_user, email_pwd)

	cases = getEntries('https://'+company+'.desk.com/api/v2/cases/search?status=open,pending')
	users = getEntries('https://'+company+'.desk.com/api/v2/users')

	opencases = {}

	for user in users:
		opencases[user['_links']['self']['href']] = {'email' : user['email'], 'name' : user['name'], 'cases' : [] }

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
			header = 'From: %s\nTo: %s\nSubject: %s\n' % (gmail_user, email, 'Open Cases on Desk.com')
			text = header + text
			try:
				server.sendmail(email_user, email, text)
				print text
				print 'Sent email'
			except:
				print 'failed to send'
			
def getEntries(url):
	r = requests.get(url, auth=(user,password))
	data = json.loads(r.text)
	entries =  data['_embedded']['entries']
	return entries

if __name__ == '__main__':
	main()