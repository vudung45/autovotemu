import requests
import re
import json
import threading
import time
from random import choice
from config import CONFIG
accounts = []
proxies = []
balance = {}

with open("balance.json") as fo:
	balance = json.loads(fo.read())

with open("accounts.txt") as fo:
	lines = fo.read().splitlines()
	for line in lines:
		accounts += line.split(" ")

with open("proxies.txt") as fo:
	proxies = fo.read().splitlines()


def get_info(username, password, lock):
	sess = requests.session()

	login = False
	text = ""
	print("Get balance for: "+username)
	while not login:
		try:
			proxy = {}
			if CONFIG.VOTE.login_proxy:
				proxy = {'https': choice(proxies)}
			text = sess.post('https://globalmu.net/account-panel/login', {
				  "username" :  username,
				  "password": password,
				  "server": 'X50'
				}, proxy, timeout=10).text
		except Exception as e:
			print(e)
			continue

		if "My Credits" not in text:
			if "Wrong username" in text:
				print("Wrong password/username for account: "+ username)
				return
			login = False
			print(text)
			print("Login failed account:" + username)
			time.sleep(2)
		else:
			print("Logged in successfully to account: "+username)
			login = True

	regex = r"<span id=\"my_credits\">(.+)</span>"
	lock.acquire()
	try:
		balance[username] = int(re.search(regex,text).group(1))
		with open("balance.json", "w") as f:
			f.write(json.dumps(balance))
	except:
		print(username)
	lock.release()

lock = threading.Lock()
n_threads = 10
print(balance)
for t in range(0,len(accounts),2 * n_threads):
	threads = []
	for i in range(t,min(len(accounts) -1,t+2*n_threads),2):
			try :
				if accounts[i] not in balance:
					thread = threading.Thread(target = get_info, args=(accounts[i],accounts[i+1], lock,))
					threads.append(thread)
					thread.start()
					time.sleep(2)
			except KeyboardInterrupt:
				break
			except:
				continue
	for thread in threads:
		thread.join()

