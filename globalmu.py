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
shuffle(black_list)

def vote(username,password, proxies, lock):
	sess = requests.session()

	print("Voting for acc: "+username)

	proxy = None
	if username not in balance:
		balance[username] = 0


	#login to account
	proxy = {}
	if CONFIG.VOTE.login_proxy:
		proxy = {'https': choice(proxies)}
	if(not login(username, password,sess, proxy)):
		return

	#finished log in now add this account to ignore
	lock.acquire()
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
				bonus = vote_request(sess,id, proxy)
				if proxy not in black_list: # add latest proxy if hasnt been added
					lock.acquire()
					black_list.append(proxy)
					with open("blacklist.txt", "a+") as f:
						f.write(proxy+"\n")
						print("Blacklisting: "+proxy)
					lock.release()
				if bonus != -1:
					success = True
					balance[username] += bonus
				else:
					lock.acquire()
					proxy = proxies.pop(0)
					lock.release()
					time.sleep(1)
					continue
		lock.acquire()
		ignore.append(username)
		with open("balance.json", "w") as f:
			f.write(json.dumps(balance))
		with open("ignore.txt", "a+") as f:
			f.write(username+"\n")
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
		else:
			return -1
	except Exception as e:
		print(e)
		return -1
	return 0


lock = threading.Lock()
n_threads = 5
for t in range(0,len(accounts),2 * n_threads):
	threads = []
	for i in range(t,min(len(accounts) - 1,t+2*n_threads),2):
		try:
			if accounts[i] not in ignore:
				thread = threading.Thread(target = vote, args=(accounts[i], accounts[i+1], proxies, lock,))
				threads.append(thread)
				thread.start()
				time.sleep(2)
		except KeyboardInterrupt:
			break
		except:
			continue

	for thread in threads:
		thread.join()



