import requests
from random import shuffle, choice
import re
import json
from config import CONFIG
from utils import login, get_listings
import time
import threading

balance = {}
proxies = []
with open("proxies.txt") as fo:
	proxies = fo.read().splitlines()

with open("balance.json") as fo:
	balance = json.loads(fo.read())


balances = list(balance.values())
balances.sort(reverse=True)
print(balances)

def buy_item(username, password, items, item, ignore, lock):
	lock.acquire()
	to_buy = item[1]
	lock.release()
	print("Buy item: "+to_buy +" with account: "+username)
	sess = requests.session()

	#login to account
	if(not login(username, password,sess, proxies, CONFIG.SELL_ITEM.login_proxy)):
		return

	done = False
	proxy = {}
	while not done:
		try:
			if CONFIG.SELL_ITEM.sell_proxy:
				proxy = {'https': choice(proxies)}
			result = sess.post('https://globalmu.net/market/buy/'+to_buy, {
					  "buy_item": 1
					}, proxies = proxy, timeout = 10).text
			if "My Credits" in result:
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



	success = "successfully" in result or "Item not found in our database" in result
	if success:
		print("Successfully bought item " + to_buy +" with acc: "+ username)
		try:
			print(sess.post('https://globalmu.net/warehouse/del_item', {
						  "ajax": 1,
						  "slot": 1
						}, proxies = proxy, timeout = 10).text)
			items.remove(item)
		except:
			print("")
	else:
		print("Buying item with acc: " + username +" failed. Trying again with different account.")
		lock.acquire()
		ignore.append(username)
		if "not found" in result:
			items.remove(item)
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

def sell_item(sess, item_slot, gather_all = False):
	#get dmn_csrf
	done = False
	dmn_csrf_protection = ""
	proxy = {}

	while not done:
		proxy = {}
		if CONFIG.SELL_ITEM.sell_proxy and len(proxies) > 0:
				proxy = {"https" : choice(proxies)}
				print(proxy)
		try:

			text = sess.get("https://globalmu.net/warehouse", proxies = proxy, timeout=10).text
			regex = r"<input type=\"hidden\" name=\"dmn_csrf_protection\" value=\"(.+)\" />"
			result_find = re.findall(regex,text)
			dmn_csrf_protection = result_find[0]
			print(dmn_csrf_protection)
			done = True
			time.sleep(CONFIG.SELL_ITEM.sleep_time)
		except KeyboardInterrupt:
			break
		except:
			done = False

	
	next_item = True
	price = -1
	price_with_tax = -1
	while True:
		if next_item:
			if CONFIG.SELL_ITEM.gather_all:
				price_with_tax = balances.pop(0)
				price = int(price_with_tax / (1 + CONFIG.SELL_ITEM.tax) + 0.5)
				print("price_with_tax: "+str(price_with_tax)+" -> without tax: "+str(price))
			else:
				price = CONFIG.SELL_ITEM.price
			next_item = False

		if CONFIG.SELL_ITEM.sell_proxy and len(proxies) > 0:
				proxy = {"https" : choice(proxies)}
				print(proxy)
		try:
			text  = sess.post('https://globalmu.net/warehouse/sell_item', {
				  "dmn_csrf_protection": dmn_csrf_protection,
				  "price": price,
				  "time": 1,
				  "char": CONFIG.SELL_ITEM.char_name,
				  "payment_method": 1,
				  "server": 'X50',
				  "slot": item_slot,
				  "ajax": 1
				}, proxies = proxy, timeout = 10).text
			if "10" in text:
				if CONFIG.SELL_ITEM.gather_all:
					balances.insert(0,price_with_tax)
				break
			if 'error' in text or 'success' in text:
				next_item = True
				item_slot += 1
			print(text)

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
			if "My Credits" not in text:
				continue
			return get_listings(text)
		except Exception as e:
			print(e)
			time.sleep(CONFIG.SELL_ITEM.sleep_time)
			continue
	return []


num_turns = CONFIG.SELL_ITEM.turns if CONFIG.SELL_ITEM.auto_sell else 1
start_slot = CONFIG.SELL_ITEM.start_slot

while num_turns > 0:
	num_turns -= 1
	sess = requests.session() #sellser session
	#login to seller account
	if(not login(CONFIG.SELL_ITEM.username, CONFIG.SELL_ITEM.password,sess, proxies, CONFIG.SELL_ITEM.login_proxy)):
		break

	#start auto selling if this is enable
	if CONFIG.SELL_ITEM.auto_sell:
		start_slot = sell_item(sess, start_slot)

	#fetch sell items list
	items = get_sell_list(sess, proxies, CONFIG.SELL_ITEM.login_proxy)
	items.sort(key=lambda k : k[0], reverse=True)
	print(items)
	lock = threading.Lock()
	n_threads = 10
	while len(items) > 0:
		threads = []
		local_ignore = []
		for i in range(0, min(len(items), n_threads)):
			for username in balance:
				if username not in local_ignore  and username not in ignore  and balance[username] >= items[i][0]:

					try:
						acc_idx = accounts.index(username)
						if acc_idx != -1:
							thread = threading.Thread(target = buy_item, args=(accounts[acc_idx],accounts[acc_idx+1], items, items[i], ignore, lock,))
							threads.append(thread)
							local_ignore.append(username)
							break
						else:
							continue
					except KeyboardInterrupt:
						break
					except:
						continue
			if len(local_ignore) == 0:
				break

		for thread in threads:
			thread.start()
			time.sleep(CONFIG.SELL_ITEM.sleep_time)
		for thread in threads:
			thread.join()



