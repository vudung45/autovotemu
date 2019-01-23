import requests
import re
import json
import threading
import time
from random import choice
from config import CONFIG
from utils import login
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


def change_password(username, password, lock):
	sess = requests.session()

	print("Changing password for: "+username)
	proxy = {}
	#login to account
	text = login(username, password,sess, proxies, CONFIG.CHANGE_PASS.login_proxy)
	if text is None:
		return

	while True:
		if CONFIG.CHANGE_PASS.login_proxy and len(proxies) > 0:
				proxy = {"https" : choice(proxies)}
				print(proxy)
		try:
			text  = sess.post('https://globalmu.net/ajax/change_password', {
				  "old_password": password,
				  "new_password": CONFIG.CHANGE_PASS.new_pass,
				  "new_password2": CONFIG.CHANGE_PASS.new_pass
			}, proxies = proxy, timeout = 10).text
			print(text)
			if "success" not in text and "error" not in text:
				time.sleep(CONFIG.CHANGE_PASS.sleep_time)
				continue
			else:
				break
		except KeyboardInterrupt:
			break
		except:
			time.sleep(CONFIG.CHANGE_PASS.sleep_time)
			continue

lock = threading.Lock()
n_threads = 20
print(balance)
for t in range(0,len(accounts),2 * n_threads):
	threads = []
	for i in range(t,min(len(accounts) -1,t+2*n_threads),2):
			try :
				thread = threading.Thread(target = change_password, args=(accounts[i],accounts[i+1], lock,))
				threads.append(thread)
				thread.start()
				time.sleep(CONFIG.CHANGE_PASS.sleep_time)
			except KeyboardInterrupt:
				break
			except:
				continue
	for thread in threads:
		thread.join()

