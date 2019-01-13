import requests
import re
import json
import threading
import time
accounts = []
with open("accounts.txt") as fo:
	lines = fo.read().splitlines()
	for line in lines:
		accounts += line.split(" ")

balance = {}

def get_info(username, password, lock):
	sess = requests.session()
	sess.post('https://globalmu.net/account-panel', {
		  "username" :  username,
		  "password": password,
		  "server": 'X50'
		})

	text = sess.get('https://globalmu.net/market/history').text
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
for t in range(0,len(accounts),2 * n_threads):
	threads = []
	for i in range(t,t+2*n_threads,2):
		try :
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

