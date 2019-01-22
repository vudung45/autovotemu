import requests
import time
from random import choice
import re

def login(username, password, sess, proxies, use_proxy = False):
	proxy = {}
	if use_proxy:
		proxy = {'https': choice(proxies)}
	login = False
	text = None
	while not login:
		try:
			text = sess.post('https://globalmu.net/account-panel/login', {
				  "username" :  username,
				  "password": password,
				  "server": 'X50'
				}, proxies=proxy,timeout=10).text
		except KeyboardInterrupt:
			break
		except Exception as e:
			#print("Requests failed, trying again")
			time.sleep(2)
			if use_proxy:
				proxy = {'https': choice(proxies)}
			login = False
			continue

		if "My Credits" not in text:
			if "Wrong username" in text:
				print("Wrong password/username for account: "+ username)
				return None
			login = False
			time.sleep(2)
		else:
			print("Logged in successfully to account: "+username)
			login = True
	return text

def get_listings(text):
	text = text.replace("\n","")

	regex= r"<tr.*?>.*?<td>.*?</tr>"

	listings = re.findall(regex,text)

	items = []

	for listing in listings:
		regex= r"<tr.*?>.*?</span>.*?</td>.*?<td.*?>(.+?) Credits</td>.*?<td><a href=\"https://globalmu.net/market/remove/(.+?)\">Remove</a></td>.*?</tr>"
		result = re.findall(regex,listing)
		if len(result) == 1:
			items.append((int(result[0][0]), result[0][1]))
	return items