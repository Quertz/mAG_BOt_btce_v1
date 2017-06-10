#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import math
import sqlite3
import time
import Api
import Tapi
import Logger
import Printer
import Helper
import DataConsistence


# ------------
# Konstanty
# ------------

PAIRSDATABASE = "./0_databases/pairsinfo.db"
CANDLESDATABASE = "./0_databases/candles.db"
SIGNALSDATABASE = "./0_databases/indicators.db"
TICKERSDATABASE = "./0_databases/tickers.db"
TRADEPERMISSIONSFILE = "./0_temporary/tradespermissions.per"
COUNTERSRESETFILE = "./0_temporary/countersresetfile.per"


# ------------
# Třídy
# ------------

class TradeMethods:
	"""
	Tato třída má na starost techniky pro
	nákup a prodej měn.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.api = Api.PublicApi()
		self.tapi = Tapi.TradeApi()
		self.buyslipage = self.config.buySlipage
		self.sellslipage = self.config.sellSlipage
		self.tickerfrequency = self.config.bigtickerfreq
		self.currentfunds = self.getCurrentAccountState()
		self.currentticker = None

	def getAllPairsInfo(self):
		"""
		Získá aktuální obchodovatelné páry z databáze.
		"""
		pairsinfolist = []
		con = sqlite3.connect(PAIRSDATABASE)
		cur = con.cursor()
		for pair in cur.execute("SELECT * FROM pairs"):
			pairdict = {
				"pair": pair[0],
				"decimal": pair[1],
				"min_price": pair[2],
				"max_price": pair[3],
				"fee": pair[4],
				"min_amount": pair[5]
			}
			pairsinfolist.append(pairdict)
		con.close()
		return pairsinfolist

	def getTradingPairs(self):
		"""
		Navrátí seznam jednotlivých
		párů které obchodujeme.
		:return:
		"""
		pairsinfo = self.getAllPairsInfo()
		allpairs = []
		for i in pairsinfo:
			allpairs.append(i["pair"])
		return allpairs

	def getTradingCurrencies(self):
		"""
		Navrátí množinu jednotlivých
		měn které obchodujeme.
		:return:
		"""
		allpairs = self.getTradingPairs()
		allcurrencies = []
		for q in allpairs:
			r = q.split("_")
			for k in r:
				allcurrencies.append(k)
		# unique
		allcurrencies = set(allcurrencies)
		return allcurrencies

	def getSinglePairInfo(self, pair):
		"""
		Tato funkce získá aktuální informace
		o páru jež chceme obchodovat.
		Např: decimal, minimum atd.
		:param pair:
		:return:
		"""
		allpairsinfo = self.getAllPairsInfo()
		for i in allpairsinfo:
			if i["pair"] == pair:
				return dict(i)

	def getCurrentAccountState(self):
		"""
		Získá současný stav účtu.
		:return:
		"""
		getAccountInfo = self.tapi.getAccountInfo()
		currentfunds = dict(getAccountInfo["return"]["funds"])
		tradingcurrencies = self.getTradingCurrencies()
		currenttradingfunds = dict()
		# Pozor zde radši navracím stav účtu jen pro páry,
		# které obchodujeme, protože mi to dál v kódu dělá neplechu.
		for i in tradingcurrencies:
			newdict = {
				i: currentfunds[i]
			}
			currenttradingfunds.update(newdict)
		return currenttradingfunds

	def retrievecurrrentprices(self, pair):
		con = sqlite3.connect(TICKERSDATABASE)
		cur = con.cursor()
		newdict = {}
		nextdict = {}
		for i in cur.execute("SELECT * FROM tickers_" + pair):
			newdict["high"] = i[0]
			newdict["low"] = i[1]
			newdict["sell"] = i[2]
			newdict["buy"] = i[3]
			newdict["avg"] = i[4]
			newdict["last"] = i[5]
			newdict["vol"] = i[6]
			newdict["vol_cur"] = i[7]
		nextdict[pair] = newdict
		con.close()
		return nextdict

	def buy(self, pair, sequentialbuy):
		"""
		Metoda nákupu.
		:param pair:
		:return:
		"""

		def countPrice():
			"""
			Spočítá aktuální cenu, na základě požadavku
			api informací o posledním nákupu.
			:return:
			"""
			getticker = self.retrievecurrrentprices(pair)
			lastbuy = getticker[pair]["buy"]
			slipage = (lastbuy / 100) * self.buyslipage
			price = lastbuy + slipage
			return price

		def getCurrencyState():
			"""
			Navrátí stav měny na účtu za niž nakupujeme.
			:return:
			"""
			# Zde aktualizuji stav účtu.
			self.currentfunds = self.getCurrentAccountState()
			# Navrací seznam dvou řetězců - měn v páru.
			split = pair.split("_")
			getcurrency = split[1]
			currencyinaccount = self.currentfunds[getcurrency]
			return currencyinaccount

		def tryBuy():
			"""
			Toto je přímo funkce na spočítání ceny,
			objemu a spojenína Btc-e. Při chybovém
			návratu dojde k zaokrouhlení objemu o
			jedno desetinné číslo výš.
			:param :
			:return:
			"""
			details = self.getSinglePairInfo(pair)
			deci = details["decimal"]
			cyklecounter = 1
			while True:
				mycurrency = getCurrencyState()
				if mycurrency:
					price = countPrice()  # -5 je jen pro debugging aby k obchodům skutečně nedošlo.
					# Vydělíme stav mého účtu, stavem triplebuy:
					mycurrency = mycurrency/sequentialbuy
					tmpamount = (mycurrency / price)  # / 10 je jen pro debugging.
					amount = (math.floor(tmpamount * (10 ** deci)) / (10 ** deci))  # +3 je jen pro debugging
					if float(amount) > float(details["min_amount"] * 1.2):
						# Provede nákup.
						buy = self.tapi.trade(str(pair), str("buy"), round(float(price), deci),
						                      round(float(amount), deci))
						if buy:
							return buy, price
						else:
							# Povoluji max. 2 pokusy o zaokrouhlení.
							if cyklecounter <= 2:
								deci += 1
								cyklecounter += 1
								continue
							else:
								return False
					else:
						return False
				else:
					return False

		def getBuyIDandPrice():
			"""
			Vyzíská ID obchodu a cenu.
			:return:
			"""
			details = tryBuy()
			if details:
				tradedetails = details[0]
				price = float(details[1])
				# Aktualizuje stav účtu
				order_id = int(tradedetails["return"]["order_id"])
				return order_id, price
			else:
				return False

		def buyCykle():
			"""
			Zajistí jistý nákup měny.
			:return:
			"""
			tradingpairs = self.getTradingPairs()
			if pair in tradingpairs:
				counter = 0

				def getOrderInfo(orderID):
					"""
					Navrací informace o příkazu,
					pokud obdrží chybu, pokus opakuje
					maximálně třikrát. Po té navrátí
					False.
					:param orderID:
					:return:
					"""
					currentorderinfo = dict(self.tapi.orderInfo(orderID))
					if currentorderinfo["success"] == 1:
						for key, value in currentorderinfo["return"].items():
							newdict = {
								"status": value["status"]
							}
							return newdict

				while True:
					counter += 1
					tradeinfo = {
						"pair": pair,
						"price": None,
						"time": None
					}
					orderinfo = getBuyIDandPrice()
					if orderinfo:
						currentorderID = orderinfo[0]
						price = orderinfo[1]
						tradeinfo["price"] = price
						tradeinfo["time"] = time.asctime()
						# Nákupu bych dal cca 30 sekund.
						time.sleep(30)
						if currentorderID:
							orderstate = getOrderInfo(currentorderID)
							# Pokud návratový status je 0, pak je příkaz stále aktivní
							# a nic se nenakoupilo. Zde začínáme cykly pro nákup, v prvním
							# cyklu může být návratový status jen buď 0 = aktivní, anebo
							# 1 = vyplněn. V druhém cyklu po zrušení příkazu, může být návratový
							# status ještě, 2 = zrušen, anebo 3 = zrušen, ale částečně vyplněn.
							if orderstate["status"] == 0:
								# Pokud je návratový stav 0, rušíme objednávku.
								cancelinfo = self.tapi.CancelOrder(currentorderID)
								if cancelinfo == "Done":
									return tradeinfo
								else:
									# Nyní znovu zkontrolujeme objednávku.
									orderstate = getOrderInfo(currentorderID)
									if orderstate["status"] == 2:
										# Povoluji jen 3 opakování.
										if counter <= 3:
											continue
										else:
											if tradeinfo:
												return tradeinfo
											else:
												return False
									elif orderstate["status"] == 3:
										# Povoluji jen 3 opakování.
										if counter <= 3:
											continue
										else:
											if tradeinfo:
												return tradeinfo
											else:
												return False
									elif orderstate["status"] == 1:
										return tradeinfo
							elif orderstate["status"] == 1:
								return tradeinfo
						else:
							return tradeinfo
					else:
						return False
			else:
				return False

		return buyCykle()

	def sell(self, pair):
		"""
		Metoda pro prodej.
		:param pair:
		:return:
		"""

		def countPrice():
			"""
			Spočítá aktuální cenu, na základě požadavku
			api informací o posledním nákupu.
			:return:
			"""
			getticker = self.retrievecurrrentprices(pair)
			lastsell = getticker[pair]["sell"]
			slipage = (lastsell / 100) * self.sellslipage
			price = lastsell - slipage
			return price

		def getCurrencyState():
			"""
			Navrátí stav měny na účtu za niž nakupujeme.
			:return:
			"""
			# Zde aktualizuji stav účtu.
			self.currentfunds = self.getCurrentAccountState()
			# Navrací seznam dvou řetězců - měn v páru.
			split = pair.split("_")
			getcurrency = split[0]
			currencyinaccount = self.currentfunds[getcurrency]
			return currencyinaccount

		def trySell():
			"""
			Má na starost odprodej měny. Jeho zajištění a zacyklení.
			:return:
			"""
			details = self.getSinglePairInfo(pair)
			deci = int(details["decimal"])
			cyklecounter = 1
			while True:
				mycurrency = getCurrencyState()
				if mycurrency:
					price = countPrice()  # + 5 je jen pro debugging aby k obchodům skutečně nedošlo.
					amount = (math.floor(mycurrency * (10 ** deci)) / (10 ** deci))
					if float(amount) > float(details["min_amount"]):
						# Provede nákup.
						sell = self.tapi.trade(str(pair), str("sell"), round(float(price), deci),
						                       round(float(amount), deci))
						if sell:
							return sell, price
						else:
							if cyklecounter <= 2:
								deci += 1
								cyklecounter += 1
								continue
							else:
								return False
					else:
						return False
				else:
					return False

		def getSellIDandPrice():
			details = trySell()
			if details:
				tradedetails = details[0]
				price = float(details[1])
				order_id = int(tradedetails["return"]["order_id"])
				return order_id, price
			else:
				return False

		def sellCykle():
			"""
			Zajistí jistý prodej měny.
			:return:
			"""
			tradingpairs = self.getTradingPairs()
			if pair in tradingpairs:

				def getOrderInfo(orderID):
					"""
					Navrací informace o příkazu,
					pokud obdrží chybu, pokus opakuje
					maximálně třikrát. Po té navrátí
					False.
					:param orderID:
					:return:
					"""
					currentorderinfo = dict(self.tapi.orderInfo(orderID))
					if currentorderinfo["success"] == 1:
						for key, value in currentorderinfo["return"].items():
							newdict = {
								"status": value["status"]
							}
							return newdict

				while True:
					tradeinfo = {
						"pair": pair,
						"price": None,
						"time": None
					}
					orderinfo = getSellIDandPrice()
					if orderinfo:
						currentorderID = orderinfo[0]
						price = orderinfo[1]
						tradeinfo["price"] = price
						tradeinfo["time"] = time.asctime()
						# Prodeji bych dal cca 30 sekund.
						time.sleep(30)
						if currentorderID:
							orderstate = getOrderInfo(currentorderID)
							# Pokud návratový status je 0, pak je příkaz stále aktivní
							# a nic se neodprodalo. Zde začínáme cykly pro nákup, v prvním
							# cyklu může být návratový status jen buď 0 = aktivní, anebo
							# 1 = vyplněn. V druhém cyklu po zrušení příkazu, může být návratový
							# status ještě, 2 = zrušen, anebo 3 = zrušen, ale částečně vyplněn.
							if orderstate["status"] == 0:
								# Pokud je návratový stav 0, rušíme objednávku.
								cancelinfo = self.tapi.CancelOrder(currentorderID)
								if cancelinfo == "Done":
									return tradeinfo
								else:
									# Nyní znovu zkontrolujeme objednávku.
									orderstate = getOrderInfo(currentorderID)
									if orderstate["status"] == 2:
										continue
									elif orderstate["status"] == 3:
										continue
									elif orderstate["status"] == 1:
										return tradeinfo
							elif orderstate["status"] == 1:
								return tradeinfo
						else:
							return tradeinfo
					else:
						return False
			else:
				return False

		def checkSell():
			"""
			Zkontroluje zda bylo opravdu
			odprodáno vše. POužijeme počítadlo,
			nastavené na 5, protože nechceme, aby
			nám vznikla nechtěná nekonečná
			smyčka v případě komplikací.
			:return:
			"""
			counter = 0
			tradeinfo = sellCykle()
			details = self.getSinglePairInfo(pair)
			currencystate = getCurrencyState()
			while counter <= 5:
				if float(currencystate) > float(details["min_amount"] * 2):
					counter += 1
					tradeinfo = sellCykle()
					continue
				else:
					break
			return tradeinfo

		return checkSell()


class Trade:
	"""
	Tato třída má na starost zastřešení a správu metod
	na nákupy a prodeje. Uchovává jejich proměnné,
	výše a tisk do terrminálu i logu.
	"""

	def __init__(self):
		# Přiřazení vnějších tříd a metod.
		self.conf = Helper.Config()
		self.tapi = Tapi.TradeApi()
		self.api = Api.PublicApi()
		self.bigticker = None
		self.printer = Printer.TraderPrinter()
		self.logger = Logger.TraderLogging()
		self.methods = TradeMethods()
		self.currentfunds = self.getCurrentAccountState()
		self.initialfunds = self.currentfunds
		self.usdinitialfunds = self.getAccountStateInUSD()
		self.starttime = time.asctime()
		self.boughts = []
		self.buys = 0
		self.sells = 0
		self.losses = 0
		self.profits = 0
		self.currentticker = None

	def counterresetperm(self):
		fobj = open(COUNTERSRESETFILE, "r", encoding="UTF-8")
		r = fobj.read()
		r = eval(r)
		return r

	def pairsFromDatabase(self):
		"""
		Vyzíská páry z databáze, kam jsme je umístili abychom co nejméně
		zatěžovali servery z btc-e.
		:return:
		"""
		con = sqlite3.connect(PAIRSDATABASE)
		cur = con.cursor()
		pairs = []
		for pair in cur.execute("SELECT * FROM pairs"):
			pairs.append(pair[0])
		con.close()
		# Unique
		return set(pairs)

	def getTradingCurrencies(self):
		"""
		Navrátí množinu jednotlivých
		měn které obchodujeme.
		:return:
		"""
		allpairs = self.pairsFromDatabase()
		allcurrencies = []
		for q in allpairs:
			r = q.split("_")
			for k in r:
				allcurrencies.append(k)
		# unique
		allcurrencies = set(allcurrencies)
		return allcurrencies

	def getCurrentAccountState(self):
		"""
		Získá současný stav účtu.
		:return:
		"""
		getAccountInfo = self.tapi.getAccountInfo()
		currentfunds = dict(getAccountInfo["return"]["funds"])
		tradingcurrencies = self.getTradingCurrencies()
		currenttradingfunds = dict()
		# Pozor zde radši navracím stav účtu jen pro páry,
		# které obchodujeme, protože mi to dál v kódu dělá neplechu.
		for i in tradingcurrencies:
			newdict = {
				i: currentfunds[i]
			}
			currenttradingfunds.update(newdict)
		return currenttradingfunds

	def retrieveallcurrrentprices(self):
		con = sqlite3.connect(TICKERSDATABASE)
		cur = con.cursor()
		bigdict = {}
		for pair in self.pairsFromDatabase():
			newdict = {}
			for i in cur.execute("SELECT * FROM tickers_" + pair):
				newdict["high"] = i[0]
				newdict["low"] = i[1]
				newdict["sell"] = i[2]
				newdict["buy"] = i[3]
				newdict["avg"] = i[4]
				newdict["last"] = i[5]
				newdict["vol"] = i[6]
				newdict["vol_cur"] = i[7]
			bigdict[pair] = newdict
		con.close()
		return bigdict

	def getCurrentPrices(self, pair):
		"""
		Zjistí aktuální cenu pro zadaný pár.
		:param pair:
		:return:
		"""
		mezisoucet = 0
		self.bigticker = self.retrieveallcurrrentprices()
		bigticker = dict(self.bigticker)
		for key, value in bigticker.items():
			if key == pair:
				ticker = value
				buyprice = ticker["buy"]
				sellprice = ticker["sell"]
				mezisoucet += buyprice
				mezisoucet += sellprice
		return float(mezisoucet / 2)

	def getAccountStateInUSD(self):
		usd = 0.0
		# Aktualizujeme ceny.
		self.bigticker = self.retrieveallcurrrentprices()
		tradingpairs = self.pairsFromDatabase()
		self.currentfunds = self.getCurrentAccountState()
		for key, value in self.currentfunds.items():
			if key != "usd" and value > 0.0:
				if key != "rur":
					priceskey = (str(key), "usd")
					priceskey = "_".join(priceskey)
					if priceskey in tradingpairs:
						currentprice = self.getCurrentPrices(priceskey)
						amount = value * currentprice
						usd += amount
				elif key == "rur":
					priceskey = ("usd", str(key))
					priceskey = "_".join(priceskey)
					if priceskey in tradingpairs:
						currentprice = self.getCurrentPrices(priceskey)
						amount = value * currentprice
						usd += amount
			elif key == "usd" and value > 0.0:
				usd += value
		return usd

	def controlTrades(self, sells, buys):
		"""
		Tato metoda spravuje kompletní
		cykly pro nákupy a prodeje.
		Udržuje proměnné a statistiku
		obchodů.
		:param sells:
		:param buys:
		:return:
		"""
		overalltradesinfo = []
		self.currentfunds = self.getCurrentAccountState()
		self.bigticker = self.retrieveallcurrrentprices()

		def iteration(it):
			"""
			Naiteruje posloupnosti prodejů
			a nákupů, abychom měli jistotu,
			že se jedná o naiterovanou posloupnost.
			V případě neúspěchu navrací prázdný seznam.
			:param it:
			:return:
			"""
			if it:
				result = []
				for i in it:
					result.append(i)
				return result
			else:
				return []

		def getBoughtPairs():
			"""
			Vyextrahuje z informací o nákupech
			v self.boughts, páry, které byly nakoupeny.
			V případě neúspěchu navrací prázdný seznam.
			:return:
			"""
			pairs = []
			if self.boughts:
				for i in self.boughts:
					pairs.append(i["pair"])
				return pairs
			else:
				return set(pairs)

		# Naiterujeme prodeje a nákupy.
		sells = iteration(sells)
		buys = iteration(buys)

		# Aplikujeme tradespermissions a řízení konzistence dat.
		def readpermission():
			perm = None
			fobj = open(TRADEPERMISSIONSFILE, encoding="UTF-8")
			for line in fobj:
				perm = line.rstrip()
			fobj.close()
			return perm

		# Zprocesování permissions
		permissions = readpermission()

		# Pokud je obchodování zakázáno vyprázdníme
		# seznamy pro nákup i prodej.
		if permissions == "False":
			sells = []
			buys = []
		# Pokud máme prodat vše naplníme seznam pro sell
		# všemi nakoupenými páry a seznam pro buys vyprázdníme.
		elif permissions == "Sell":
			sells = getBoughtPairs()
			buys = []
		# Pokud máme obchodování povoleno necháme
		# vše tak jak je.
		elif permissions == "True":
			pass

		# Vlastní cyklus pro prodeje.
		if sells:
			for pi in sells:
				pair = pi["pair"]
				algorythm = pi["algorythm"]
				boughtpairs = getBoughtPairs()
				if pair in boughtpairs:
					for it in self.boughts:
						if it["pair"] == pair:
							if it["algorythm"] == algorythm or algorythm == 0:
								sellinfo = self.methods.sell(pair)
								if sellinfo:
									self.sells += 1
									sellprice = sellinfo["price"]
									self.logger.loggsell(pair, sellprice)
									selltime = sellinfo["time"]
									buyinfo = dict(it)
									self.boughts.remove(it)
									buyprice = buyinfo["price"]
									buytime = buyinfo["time"]
									costs = (
										(buyprice / 100) * float(
											self.conf.sellSlipage + self.conf.buySlipage + 0.4)
									)
									wholeinfo = {
										"pair": pair,
										"buyprice": buyprice,
										"buytime": buytime,
										"sellprice": sellprice,
										"selltime": selltime
									}
									if buyprice < sellprice - costs:
										self.profits += 1
									elif buyprice > sellprice - costs:
										self.losses += 1
									else:
										pass
									overalltradesinfo.append(wholeinfo)
				else:
					self.methods.sell(pair)
			reset = self.counterresetperm()
			if reset:
				self.currentfunds = self.getCurrentAccountState()
				self.initialfunds = self.currentfunds
				self.usdinitialfunds = self.getAccountStateInUSD()
			time.sleep(1)

		# Vlastní cyklus nákupů.
		if buys:
			reset = self.counterresetperm()
			if reset:
				self.currentfunds = self.getCurrentAccountState()
				self.initialfunds = self.currentfunds
				self.usdinitialfunds = self.getAccountStateInUSD()
			for i in buys:
				pair = i["pair"]
				algorythm = i["algorythm"]
				sequencialbuy = i["sequencialbuy"]
				boughtpairs = getBoughtPairs()
				buydata = self.methods.buy(pair, sequentialbuy=sequencialbuy)
				# Návrat:
				# 	tradeinfo = {
				#	"pair": pair,
				#	"price": None,
				#	"time": None
				#	}
				if buydata:
					newdict = {"algorythm": algorythm}
					buydata.update(newdict)
					self.boughts.append(buydata)
					self.logger.loggbuy(pair, buydata["price"])
					self.buys += 1
					continue
				else:
					pass

		self.currentfunds = self.getCurrentAccountState()
		currentinusdfunds = self.getAccountStateInUSD()
		currenttime = time.asctime()
		self.printer.printTrader(False, self.starttime, currenttime, self.usdinitialfunds, self.initialfunds,
		                         self.currentfunds, self.buys, self.sells, self.losses,
		                         self.profits, currentinusdfunds)
		return self.boughts


# ------------
# Testy:
# ------------

if __name__ == "__main__":
	# Funkce
	def mezera():
		print("#" * 70)


	def clean():
		print("\n" * 50)


	# Přiřazení instancí tříd
	tm = Trade()

	print(tm.controlTrades([], [{'algorythm': 1, 'pair': 'nmc_usd'}]))
