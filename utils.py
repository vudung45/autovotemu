import requests
import time
def login(username, password, sess, proxies, use_proxy = False):
	proxy = {}
	if CONFIG.VOTE.login_proxy:
		proxy = {'https': choice(proxies)}
	login = False
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
			print("Requests failed, trying again")
			time.sleep(2)
			continue

		if "My Credits" not in text:
			if "Wrong username" in text:
				print("Wrong password/username for account: "+ username)
				return False
			login = False
			print("Login failed account:" + username)
			time.sleep(2)
		else:
			print("Logged in successfully to account: "+username)
			login = True
	return True