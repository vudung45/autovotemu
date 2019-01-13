import requests
from random import shuffle, choice
import re
import json
from config import CONFIG
import time
import threading

balance = {}
proxies = []
with open("proxies.txt") as fo:
	proxies = fo.read().splitlines()

with open("balance.json") as fo:
	balance = json.loads(fo.read())


#login to seller account
sess = requests.session()
sess.post('https://globalmu.net/account-panel/login', {
	  "username" :  CONFIG.SELL_ITEM.username,
	  "password": CONFIG.SELL_ITEM.password,
	  "server": 'X50'
	},timeout = 10)



#start selling
if CONFIG.SELL_ITEM.auto_sell:
	time.sleep(1)
	text = sess.get("https://globalmu.net/warehouse").text
	regex = r"<input type=\"hidden\" name=\"dmn_csrf_protection\" value=\"(.+)\" />"
	result_find = re.findall(regex,text)
	dmn_csrf_protection = ""
	if len(result_find) > 0:
		dmn_csrf_protection = result_find[0]
		print(dmn_csrf_protection)

	item_slot = CONFIG.SELL_ITEM.start_slot
	while item_slot < CONFIG.SELL_ITEM.start_slot + CONFIG.SELL_ITEM.num_sell:
		proxy = {}
		try:
			if CONFIG.SELL_ITEM.use_proxy and len(proxies):
				proxy = {"https" : choice(proxies)}
				print(proxy)
			print(sess.post('https://globalmu.net/warehouse/sell_item', {
				  "dmn_csrf_protection": dmn_csrf_protection,
				  "price": 40,
				  "time": 1,
				  "char": CONFIG.SELL_ITEM.char_name,
				  "payment_method": 1,
				  "server": 'X50',
				  "slot": item_slot,
				  "ajax": 1
			}, proxies = proxy, timeout = 10).text)
			item_slot += 1
		except:
			print("Trying again...")

text = sess.get('https://globalmu.net/market/history').text
regex = r"https://globalmu.net/market/remove/(......)"
start = re.findall(regex,text)
print(start)


def buy_item(user, password, items, ignore, lock):
	lock.acquire()
	to_buy = items.pop(0)
	lock.release()
	print("Buy item: "+str(to_buy) +" with account: "+user)
	sess = requests.session()
	try:
		text = sess.post('https://globalmu.net/account-panel/login', {
			  "username" :  user,
			  "password": password,
			  "server": 'X50'
			}, timeout=10).text
		if "My Credits" not in text:
			lock.acquire()
			items.append(to_buy)
			lock.release()
			print("login failed")
			return
	except:
		lock.acquire()
		items.append(to_buy)
		lock.release()
		print("login failed")

		return

	try:
		result = sess.post('https://globalmu.net/market/buy/'+str(to_buy), {
				  "buy_item": 1
				}, timeout = 10).text
	except:
		print("something went wrong while trying to buy item")
		lock.acquire()
		items.append(to_buy)
		lock.release()
		return
	#update balance
	regex = r"<span id=\"my_credits\">(.+)</span>"
	#update balance
	try:
		new_balance = int(re.search(regex,result).group(1).replace(',',''))
		print("Account "+user+"  balance: "+str(new_balance))
		balance[user] = new_balance
		with open("balance.json", "w") as f:
			f.write(json.dumps(balance))
	except:
		print("fail to upload balance")

	success = "successfully" in result
	if success:
		print("success")
		regex = r"<span id=\"my_credits\">(.+)</span>"
	else:
		print("failed, trying again with different account")
		lock.acquire()
		ignore.append(user)
		items.append(to_buy)
		lock.release()
		return


	return to_buy

accounts = []
ignore = []
with open("accounts.txt") as fo:
	lines = fo.read().splitlines()
	shuffle(lines)
	for line in lines:
		accounts += line.split(" ")


lock = threading.Lock()
n_threads = 5
while len(start) > 0:
	threads = []
	local_ignore = []
	for i in range(0, min(len(start), n_threads)):
		for username in balance:
			if username not in local_ignore and balance[username] >= CONFIG.SELL_ITEM.price :
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
		time.sleep(1)
	for thread in threads:
		thread.join()



