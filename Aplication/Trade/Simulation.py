#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import math
import sqlite3
import time
import Logger
import Printer
import Helper


# ------------
# Konstanty
# ------------

PAIRSDATABASE = "./0_databases/pairsinfo.db"
CANDLESDATABASE = "./0_databases/candles.db"
SIGNALSDATABASE = "./0_databases/indicators.db"
CURRENTTICKERFILE = "./0_temporary/currentticker.txt"
TRADEPERMISSIONSFILE = "./0_temporary/tradespermissions.per"


# ------------
# Třídy
# ------------

class Trade:
	"""
	Tato třída má na starost nákupy a prodeje měn,
	v simulačním módu.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.bigticker = None
		self.buyslipage = self.config.buySlipage
		self.sellslipage = self.config.sellSlipage
		self.logger = Logger.TraderLogging()
		self.printer = Printer.TraderPrinter()
		self.buys = 0
		self.sells = 0
		self.losses = 0
		self.profits = 0
		self.trades = 0
		self.cykles = 1
		self.starttime = time.asctime()
		self.initialfunds = self.getAccountState()
		self.initializedDolars = self.getAccountStateInUSD(self.initialfunds)
		self.currentfunds = self.getAccountState()
		self.currentDolars = self.getAccountStateInUSD(self.currentfunds)
		self.boughts = list()

	def getAllPairsInfo(self):
		"""
		Získá aktuální obchodovatelné páry z btc-e.com
		pomocí modulu api.py.
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
		return pairsinfolist

	def getSinglePairInfo(self, pair):
		"""
		Tato funkce získá aktuální informace
		o páru jež chceme obchodovat.
		Např: decimal, minimum atd.
		:return:
		"""
		for i in self.getAllPairsInfo():
			if i["pair"] == pair:
				return i

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

	def currenciesFromDatabase(self):
		"""
		Vyextrahuje jednotlivé měny z databáze.
		Tyto měny nejsou všemi měnami, které můžeme mít
		na btc_e, ale pouze všechny měny se kterými se
		aktuálně obchoduje.
		:return:
		"""
		tmp = []
		for pair in self.pairsFromDatabase():
			split = pair.split("_")
			for i in split:
				tmp.append(i)
		tmp = set(tmp)
		return tmp

	def getAccountState(self):
		"""
		Tato metoda navrací stav fiktivního
		účtu na Btc-e. Ten je nastaven v settings.ini.
		:return:
		"""
		ndict = dict()
		pairs = self.currenciesFromDatabase()
		usd = float(self.config.initialDolars)
		funds = dict()
		for i in pairs:
			if i != "usd":
				ndict = {str(i): float(0.0)}
			elif i == "usd":
				ndict = {str(i): usd}
			funds.update(ndict)
		return funds

	def retrieveallcurrrentprices(self):
		"""
		Navrací slovník současných cen
		pro daný pár. Slovník načetl
		za souboru současného tickeru.

		:param pair:
		:return:
		"""
		tick = None
		fobj = open(CURRENTTICKERFILE, encoding="UTF-8")
		for line in fobj:
			tick = eval(line.rstrip())
		fobj.close()
		return tick

	def getRealPrices(self):
		"""
		Navrátí slovník aktuálních reálních
		cen.
		:param pair:
		:return:
		"""

		ticker = self.retrieveallcurrrentprices()
		currprices = {}
		for key, value in ticker.items():
			mezisoucet = 0
			pair = str(key)
			buyprice = value["buy"]
			sellprice = value["sell"]
			mezisoucet += buyprice
			mezisoucet += sellprice
			avgprice = float(mezisoucet / 2)
			currprices[pair] = avgprice
		return currprices

	def getAccountStateInUSD(self, funds):
		"""
		Z parametru 'funds', vypočítává aktuální
		stav účtu po přepočtu na USD. K tomu využívá
		stav současných cen jednotlivých párů na Btc-e.
		Parametrem je 'funds' z toho důvodu, že jednou budu
		potřebovat vypočítat reálný stav účtu (při inicializaci)
		a příště zase simulační stav účtu.
		:param funds:
		:return:
		"""
		usd = 0.0
		funds = dict(funds)
		currprices = self.getRealPrices()
		for key, value in funds.items():
			if key != "usd" and value > 0.0:
				if key != "rur":
					priceskey = (str(key), "usd")
					priceskey = "_".join(priceskey)
					if priceskey in self.pairsFromDatabase():
						currentprice = currprices[priceskey]
						amount = value * currentprice
						usd += amount
				elif key == "rur":
					priceskey = ("usd", str(key))
					priceskey = "_".join(priceskey)
					if priceskey in self.pairsFromDatabase():
						currentprice = currprices[priceskey]
						amount = value * currentprice
						usd += amount
			elif key == "usd" and value > 0.0:
				usd += value
		return usd

	def buy(self, pairset):
		"""
		Metoda nákupu.
		:param pair:
		:return:
		"""

		pair = str(pairset["pair"])
		algorythm = int(pairset["algorythm"])

		# noinspection PyTypeChecker
		def countPrice():
			"""
			Spočítá aktuální cenu, na základě požadavku
			api informací o posledním nákupu.
			:return:
			"""
			getticker = self.retrieveallcurrrentprices()
			getticker = getticker[pair]
			lastbuy = getticker["buy"]
			slipage = (lastbuy / 100) * self.buyslipage
			price = float(lastbuy + slipage)
			return price

		def tryBuy():
			boughtinfo = {}
			# Stav měny na účtě.
			split = pair.split("_")
			buyingforcurrency = split[1]
			boughtcurrency = split[0]
			mycurrency = self.currentfunds[buyingforcurrency]
			if mycurrency:
				price = countPrice()
				details = self.getSinglePairInfo(pair)
				deci = details["decimal"]
				tmpamount = (mycurrency / price)
				amount = (math.floor(tmpamount * (10 ** deci)) / (10 ** deci))  # +3 je jen pro debugging
				if float(amount) > float(details["min_amount"]):
					for key, value in self.currentfunds.items():
						# Odečteme z účtu množství měny za které jsme nakupovali.
						if key == buyingforcurrency:
							value -= (amount * price)
							newdict = {}
							newdict[key] = value
							self.currentfunds.update(newdict)
						# Přičteme k účtu množství koupené měny.
						elif key == boughtcurrency:
							value += amount
							newdict = {}
							newdict[key] = value
							self.currentfunds.update(newdict)
					boughtinfo = {
						"pair": pair,
						"price": price,
						"time": time.asctime(),
						"algorythm": algorythm
					}
					self.buys += 1
					self.trades += 1
					self.boughts.append(boughtinfo)
					return boughtinfo
				else:
					return False
			else:
				return False

		return tryBuy()

	def sell(self, pairset):
		"""
		Metoda nákupu.
		:param pair:
		:return:
		"""
		pair = str(pairset["pair"])
		algorythm = int(pairset["algorythm"])

		# noinspection PyTypeChecker
		def countPrice():
			"""
			Z tickeru všech párů vyextrahuje ticker
			pro zadaný pár a spočítá cenu.
			:return:
			"""
			prices = self.retrieveallcurrrentprices()
			getticker = prices[pair]
			lastsell = float(getticker["sell"])
			slipage = float((lastsell / 100) * self.sellslipage)
			price = float(lastsell) - float(slipage)
			return price

		def trySell():
			"""
			Tato funkce má na starost vlastní výpočet prodeje.
			Aktualizuje stav účtu a navrací prodejní informace.
			:return:
			"""
			sellinfo = {}
			split = pair.split("_")
			sellingforcurrency = split[1]
			currency4sell = split[0]
			# Stav měny na účtě.
			mycurrency = self.currentfunds[currency4sell]
			if mycurrency:
				for i in self.boughts:
					if i["pair"] == pair and i["algorythm"] == algorythm or i["algorythm"] == 0:
						price = countPrice()
						details = self.getSinglePairInfo(pair)
						deci = details["decimal"]
						amount = (math.floor(mycurrency * (10 ** deci)) / (10 ** deci))
						if float(amount) > float(details["min_amount"]):
							for key, value in self.currentfunds.items():
								if key == currency4sell:
									value -= amount
									newdict = {}
									newdict[key] = value
									self.currentfunds.update(newdict)
								elif key == sellingforcurrency:
									value += amount * price
									newdict = {}
									newdict[key] = value
									self.currentfunds.update(newdict)
							sellinfo = {
								"pair": pair,
								"price": price,
								"time": time.asctime(),
								"algoryth": algorythm
							}
							# Nyní spočteme profit či ztrátu:
							buyprice = i["price"]
							sellprice = sellinfo["price"]
							if buyprice < sellprice:
								self.profits += 1
							else:
								self.losses += 1
							self.boughts.remove(i)
							self.sells += 1
							self.trades += 1
							return sellinfo
						else:
							return False
			else:
				return False

		return trySell()

	def controlTrades(self, sells, buys):
		"""
		Tato metoda spravuje nákupy i prodeje.
		Metody pro nákup i prodej mudejí být volány
		jen touto metodou. Protože spravuje i další
		proměnné třídy.
		:return:
		"""
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
			if self.boughts:
				pairs = []
				for i in self.boughts:
					for key, value in i.items():
						if key == "pair":
							pairs.append(value)
				return pairs
			else:
				return []

		# Naiterujeme prodeje a nákupy.
		sells = iteration(sells)
		buys = iteration(buys)
		boughtpairs = getBoughtPairs()

		# Aplikujeme tradespermissions a řízení konzistence dat.
		def readpermission():
			perm = None
			fobj = open(CURRENTTICKERFILE, encoding="UTF-8")
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

		if sells:
			for pairset in sells:
				pair = pairset["pair"]
				sed = self.sell(pairset)
				if sed:
					self.logger.loggsell(pair, sed["price"])
				else:
					pass
		else:
			pass

		if buys:
			for pairset in buys:
				pair = pairset["pair"]
				sed = self.buy(pairset)
				if sed:
					self.logger.loggbuy(pair, sed["price"])
				else:
					pass
		else:
			pass

		currentinusdfunds = self.getAccountStateInUSD(self.currentfunds)
		currenttime = time.asctime()
		self.printer.printTrader(True, self.starttime, currenttime, self.initializedDolars, self.initialfunds,
		                         self.currentfunds, self.buys, self.sells, self.losses,
		                         self.profits, currentinusdfunds)
