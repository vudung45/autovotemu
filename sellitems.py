import requests
from random import shuffle, choice
import re
import json
from config import CONFIG
from utils import login
import time
import threading

balance = {}
proxies = []
with open("proxies.txt") as fo:
	proxies = fo.read().splitlines()

with open("balance.json") as fo:
	balance = json.loads(fo.read())



def buy_item(username, password, items, ignore, lock):
	lock.acquire()
	to_buy = items.pop(0)
	lock.release()
	print("Buy item: "+str(to_buy) +" with account: "+username)
	sess = requests.session()

	#login to account
	if(not login(username, password,sess, proxies, CONFIG.SELL_ITEM.login_proxy)):
		return

	done = False
	while not done:
		proxy = {}
		try:
			if CONFIG.SELL_ITEM.sell_proxy:
				proxy = {'https': choice(proxies)}
			result = sess.post('https://globalmu.net/market/buy/'+str(to_buy), {
					  "buy_item": 1
					}, proxies = proxy, timeout = 10).text
			done = True
		except KeyboardInterrupt:
			break
		except:
			time.sleep(3)
	#update balance
	regex = r"<span id=\"my_credits\">(.+)</span>"
	#update balance
	try:
		new_balance = int(re.search(regex,result).group(1).replace(',',''))
		print("Account "+username+"  balance: "+str(new_balance))
		balance[username] = new_balance
		with open("balance.json", "w") as f:
			f.write(json.dumps(balance))
	except:
		print("fail to upload balance ("+username+")")
		return -1



	success = "successfully" in result
	if success:
		print("Successfully bought item " + to_buy +" with acc: "+ username)
		print(sess.post('https://globalmu.net/warehouse/del_item', {
					  "ajax": 1,
					  "slot": 1
					}, proxies = proxy, timeout = 10).text)
	else:
		lock.acquire()
		ignore.append(username)
		if "not found" not in result:
			items.append(to_buy)
		lock.release()
		return -1


	return to_buy

accounts = []
ignore = []
with open("accounts.txt") as fo:
	lines = fo.read().splitlines()
	shuffle(lines)
	for line in lines:
		accounts += line.split(" ")

def sell_item(sess, item_slot):
	#get dmn_csrf
	done = False
	dmn_csrf_protection = ""
	while not done:
		proxy = {}
		if CONFIG.SELL_ITEM.sell_proxy and len(proxies) > 0:
				proxy = {"https" : choice(proxies)}
				print(proxy)
		try:

			text = sess.get("https://globalmu.net/warehouse", proxies = proxy).text
			regex = r"<input type=\"hidden\" name=\"dmn_csrf_protection\" value=\"(.+)\" />"
			result_find = re.findall(regex,text)
			dmn_csrf_protection = ""
			dmn_csrf_protection = result_find[0]
			print(dmn_csrf_protection)
			done = True
			time.sleep(CONFIG.SELL_ITEM.sleep_time)
		except KeyboardInterrupt:
			break
		except:
			done = False

	while True:
		proxy = {}
		if CONFIG.SELL_ITEM.sell_proxy and len(proxies) > 0:
				proxy = {"https" : choice(proxies)}
				print(proxy)
		try:
			text  = sess.post('https://globalmu.net/warehouse/sell_item', {
				  "dmn_csrf_protection": dmn_csrf_protection,
				  "price": CONFIG.SELL_ITEM.price,
				  "time": 1,
				  "char": CONFIG.SELL_ITEM.char_name,
				  "payment_method": 1,
				  "server": 'X50',
				  "slot": item_slot,
				  "ajax": 1
				}, proxies = proxy, timeout = 10).text
			print(text)
			if "10" in text:
				break
			if '"error"'in text or '"success"' in text:
				item_slot += 1
			time.sleep(CONFIG.SELL_ITEM.sleep_time)
		except KeyboardInterrupt:
			break
		except:
			time.sleep(1)
			print("Trying again...")
	
	return item_slot

def get_sell_list(sess, proxies, use_proxy):
	while True:
		proxy = {}
		if use_proxy and len(proxies) > 0:
			proxy = {'https': choice(proxies)}
		login = False
		try:
			text = sess.get('https://globalmu.net/market/history', proxies = proxy, timeout = 10).text
			regex = r"https://globalmu.net/market/remove/(......)"
			start = re.findall(regex,text)
			return start
		except:
			time.sleep(CONFIG.SELL_ITEM.sleep_time)
			continue
	return []


num_turns = CONFIG.SELL_ITEM.turns if CONFIG.SELL_ITEM.auto_sell else 1
start_slot = CONFIG.SELL_ITEM.start_slot

while num_turns > 0:
	num_turns -= 1
	sess = requests.session() #sellser session
	#login to seller account
	if(not login(username, password,sess, proxies, CONFIG.SELL_ITEM.login_proxy)):
		break

	#start auto selling if this is enable
	if CONFIG.SELL_ITEM.auto_sell:
		start_slot = sell_item(sess, start_slot)

	#fetch sell items list
	start = get_sell_list(sess)
	print(start)
	lock = threading.Lock()
	n_threads = 5
	while len(start) > 0:
		threads = []
		local_ignore = []
		for i in range(0, min(len(start), n_threads)):
			for username in balance:
				if username not in local_ignore  and username not in ignore and balance[username] >= int(round(CONFIG.SELL_ITEM.price * 1.01)) :
					acc_idx = accounts.index(username)
					if acc_idx != -1:
						thread = threading.Thread(target = buy_item, args=(accounts[acc_idx],accounts[acc_idx+1], start, ignore, lock,))
						threads.append(thread)
						local_ignore.append(username)
						break
					else:
						continue

		for thread in threads:
			thread.start()
			time.sleep(CONFIG.SELL_ITEM.sleep_time)
		for thread in threads:
			thread.join()



