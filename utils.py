import requests
import time
from random import choice
import re
from captcha import resolve
from shutil import copyfile
def login(username, password, sess, proxies, use_proxy = False, use_image_proxy = True, solve_captcha = True):
	proxy = {}
	if use_proxy:
		proxy = {'https': choice(proxies)}
	login = False
	text = None
	invalid_code = True
	while not login:
		code = ""
		if solve_captcha and invalid_code:
			while True:
				image_proxy = {}
				if use_image_proxy:
					image_proxy = {'https': choice(proxies)}
				try: 
					r = sess.get("https://globalmu.net/captcha", proxies=image_proxy, timeout = 10,stream=True)
					if r.status_code == 200:
					    with open("./captchas/"+username+".png", 'wb') as f:
					        for chunk in r:
					            f.write(chunk)
					    invalid_code = False
					else:
						time.sleep(0.5)
						continue
				except KeyboardInterrupt:
					break
				except:
					time.sleep(0.5)
					continue

				code = resolve("./captchas/"+username+".png")
				if(len(code) == 5):
					break
				else:
					time.sleep(0.5)

			print(code)

		while True:
			try:
				text = sess.post('https://globalmu.net/ajax/login', {
					  "username" :  username,
					  "password": password,
					  "server": 'X50',
					  "code": code
					}, proxies=proxy,timeout=10).text
				break
			except KeyboardInterrupt:
				break
			except Exception as e:
				#print("Requests failed, trying again")
				time.sleep(2)
				if use_proxy:
					proxy = {'https': choice(proxies)}
				login = False
				continue

		if "success" in text or "already logged in" in text:
			print("Logged in successfully to account: "+username)
			break
		if "Invalid code" in text:
			invalid_code = True
			print("Wrong code: "+code)
			copyfile("./captchas/"+username+".png", "./captchas_wrong/"+username+".png")
		if "Wrong" in text:
			print(text)
			return None
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

if __name__=="__main__":
	with open("proxies.txt") as fo:
		proxies = fo.read().splitlines()
		sess = requests.session()
		login("davidvu4","cayzen888", sess, proxies, False, True)
