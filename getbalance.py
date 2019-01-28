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


def get_info(username, password, lock):
	sess = requests.session()

	print("Get balance for: "+username)
	#login to account
	text = login(username, password,sess, proxies, CONFIG.GET_BALANCE.login_proxy)
	if text is None:
		return



	while True:
		try:
			proxy = {}
			if CONFIG.GET_BALANCE.login_proxy:
				proxy = {"https" : choice(proxies)}
				print(proxy)

			text = sess.get("https://globalmu.net/",proxies = proxy, timeout=10).text
			if "My Credits"	in text:
				break
		except KeyboardInterrupt:
			break
		except:
			time.sleep(1)

	regex = r"<span id=\"my_credits\">(.+)</span>"
	lock.acquire()
	try:
		new_balance =  int(re.search(regex,text).group(1).replace(",",""))
		balance[username] = new_balance
		print("Account "+username+"  balance: "+str(new_balance))

		with open("balance.json", "w") as f:
			f.write(json.dumps(balance))
	except:
		print(username)
	lock.release()

lock = threading.Lock()
n_threads = 20
print(balance)
for t in range(0,len(accounts),2 * n_threads):
	threads = []
	for i in range(t,min(len(accounts) -1,t+2*n_threads),2):
			try :
				thread = threading.Thread(target = get_info, args=(accounts[i],accounts[i+1], lock,))
				threads.append(thread)
				thread.start()
				time.sleep(CONFIG.GET_BALANCE.sleep_time)
			except KeyboardInterrupt:
				break
			except:
				continue
	for thread in threads:
		thread.join()

