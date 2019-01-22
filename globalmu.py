import requests
import threading
import time
import json
from random import choice, shuffle
from config import CONFIG
from utils import login

#Parse basic settings
vote_ids = [38,48,52,53]
proxies = []
black_list = []
accounts = []
ignore = []
balance = {}

with open("proxies.txt") as fo:
	proxies = fo.read().splitlines()

print(proxies)

with open("blacklist.txt") as fo:
	black_list = fo.read().splitlines()

with open("balance.json") as fo:
	balance = json.loads(fo.read())


with open("accounts.txt") as fo:
	lines = fo.read().splitlines()
	for line in lines:
		accounts += line.split(" ")

with open("ignore.txt") as fo:
	ignore = fo.read().splitlines()


def vote(username,password, proxies, lock):
	sess = requests.session()

	print("Voting for acc: "+username)

	proxy = None
	if username not in balance:
		balance[username] = 0


	#login to account
	if(not login(username, password,sess, proxies, CONFIG.VOTE.login_proxy)):
		return
	#finished log in now add this account to ignore
	lock.acquire()
	if username not in ignore:
		ignore.append(username)
		with open("ignore.txt", "a+") as f:
			f.write(username+"\n")
	lock.release()


	lock.acquire()
	while len(proxies) > 0:
		proxy = proxies.pop(0)
		if proxy not in black_list:
			break
	lock.release()

	if proxy is not None:
		for id in vote_ids:
			#try until succeed
			success = False
			while not success and len(proxies) > 0:
				lock.acquire()
				if proxy not in black_list: # add latest proxy if hasnt been added
					black_list.append(proxy)
					with open("blacklist.txt", "a+") as f:
						f.write(proxy+"\n")
						print("Blacklisting: "+proxy)
				lock.release()
				bonus = vote_request(sess,id, proxy)
				if bonus != -1:
					success = True
					balance[username] += bonus
				else:
					lock.acquire()
					while len(proxies) > 0:
						proxy = proxies.pop(0)
						if proxy not in black_list:
							break
					lock.release()
					time.sleep(CONFIG.VOTE.sleep_time)
					continue
			time.sleep(CONFIG.VOTE.vote_sleep)
		lock.acquire()
		with open("balance.json", "w") as f:
			f.write(json.dumps(balance))
		lock.release()
		print("Finished voting for:" +username);

def vote_request(sess, id, proxy):
	print("using proxy: "+proxy)
	try: 
		result = sess.post('https://globalmu.net/ajax/vote',
			{
				"vote": id
			}, proxies={'https':proxy}, timeout=10).json()
		print(result)
		if 'success' in result: 
			return 10
	except Exception as e:
		print("Vote request failed... trying again")
		return -1
	return 0


lock = threading.Lock()
n_threads = 20
for t in range(0,len(accounts),2 * n_threads):
	threads = []
	for i in range(t,min(len(accounts) - 1,t+2*n_threads),2):
		try:
			if accounts[i] not in ignore:
				thread = threading.Thread(target = vote, args=(accounts[i], accounts[i+1], proxies, lock,))
				threads.append(thread)
				thread.start()
				time.sleep(CONFIG.VOTE.sleep_time)
		except KeyboardInterrupt:
			break
		except:
			continue

	for thread in threads:
		thread.join()



