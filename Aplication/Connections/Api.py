#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import http.client
import json
import time
import sqlite3
import Logger


# ------------
# Konstanty
# ------------

PAIRSDATABASE = "./0_databases/pairsinfo.db"
CANDLESDATABASE = "./0_databases/candles.db"
SIGNALSDATABASE = "./0_databases/indicators.db"


# ------------
# Třídy
# ------------

class PublicApi:
	"""
	Btc-e public api.
	"""

	def __init__(self):
		self.tickerDict = {}
		self.logging = Logger.ApiLogging()

	def getPublicInfo(self, param="info"):
		"""
		Navrací veřejné informace z btc-e.com. Argument je jen jeden 'info'.
		Tudíž na tento formát API dostaneme jen jednu možnou odpověd.
		Návratová informace obsahuje slovník s daty o současných měnových párech,
		maximu desetinných míst, minimum a maximum price, minimální velikost transakce.
		a poplatek u každého páru.
		:param param:
		:return dict:
		"""
		while True:
			try:
				conn = http.client.HTTPSConnection("btc-e.com", timeout=5)
				conn.request("GET", "/api/3/" + param)
				response = conn.getresponse().read().decode()
				data = json.loads(response)
				conn.close()
				return data
			except http.client.HTTPException as e:
				self.logging.logapiconnectionerror(e)
				time.sleep(3)
				continue
			except Exception as e:
				self.logging.logapiconnectionerror(e)
				time.sleep(3)
				continue

	def getPublicParam(self, param, pair):
		"""
		Obecná funkce jejíž proměnnou 'param' přiřazujeme metody pro veřejné
		API na btc-e.com jako:
		ticker, depth, trades.
		:param param:
		:param pair:
		:return dict:
		"""
		while True:
			try:
				conn = http.client.HTTPSConnection("btc-e.com", timeout=3)
				conn.request("GET", "/api/3/" + param + "/" + pair + "?ignore_invalid=1")
				response = conn.getresponse().read().decode()
				data = json.loads(response)
				conn.close()
				return data
			except http.client.HTTPException as e:
				self.logging.logapiconnectionerror(e)
				return False
			except Exception as e:
				self.logging.logapiconnectionerror(e)
				return False

			#####################################################################
			#
			# V následujících metodách přistupujeme k informacím z trhu,
			# tím způsobem, že pokud dojde k přerušení spojení, metody
			# sami se zacyklí dokud informaci nedostaneme. Pokud chceme
			# při chybě spojení dostat radši návratovou hodnotu False,
			# musíme se připojit přímo k metodě 'getPublicParam(self, param, pair)
			# a zadat parametr požadavku ručně.
			#
			#####################################################################

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

	def tickerSinglePair(self, pair):
		"""
		Navrací ticker slovník pro jeden pár.
		"""
		counter = 1
		while True:
			raw = self.getPublicParam("ticker", pair)
			if raw:
				return raw
			else:
				counter += 1
				if counter > 10:
					self.logging.logapimethoderror("tickerSinglePair", counter)
				time.sleep(1)
				continue

	def tickerAllPairs(self, allpairs=None):
		"""
		Navrací ticker slovník pro všechny páry.
		"""
		counter = 1
		while True:
			if allpairs is None:
				allpairs = self.pairsFromDatabase()
			allstring = "-".join(allpairs)
			ticker = self.getPublicParam("ticker", allstring)
			if ticker:
				return ticker
			else:
				counter += 1
				if counter > 10:
					self.logging.logapimethoderror("tickerAllPairs", counter)
				time.sleep(1)
				continue

	def singleDepth(self, pair):
		"""
		Navrací ticker slovník pro 'depth' jednoho páru.
		"""
		counter = 1
		while True:
			raw = self.getPublicParam("depth", pair)
			if raw:
				return raw
			else:
				counter += 1
				if counter > 10:
					self.logging.logapimethoderror("singleDepth", counter)
				time.sleep(1)
				continue

	def allDepth(self):
		"""
		Navrací ticker slovník pro 'depth' všech párů.
		"""
		counter = 1
		while True:
			allpairs = self.pairsFromDatabase()
			allstring = "-".join(allpairs)
			depth = self.getPublicParam("depth", allstring)
			if depth:
				return depth
			else:
				counter += 1
				if counter > 10:
					self.logging.logapimethoderror("allDepth", counter)
				time.sleep(1)
				continue

	def trades(self, pair):
		"""
		Navrací ´trades' slovník jednoho páru
		"""
		counter = 1
		while True:
			trades = self.getPublicParam("trades", pair)
			if trades:
				return trades
			else:
				counter += 1
				if counter > 10:
					self.logging.logapimethoderror("trades", counter)
				time.sleep(1)
				continue

	def getLast(self, pair):
		"""
		Navrací nejaktuálnější cenu zadaného měnového páru.
		"""
		counter = 1
		while True:
			currtrades = self.trades(pair)
			if currtrades:
				price = currtrades[pair][0]["price"]
				return price
			else:
				counter += 1
				if counter > 10:
					self.logging.logapimethoderror("getLast", counter)
				time.sleep(1)
				continue

	def getLastID(self, pair):
		"""
		Vrací ID poslední obchodu, zadaného páru.
		"""
		counter = 1
		while True:
			currtrades = self.trades(pair)
			if currtrades:
				tradeID = currtrades[pair][0]["tid"]
				return tradeID
			else:
				counter += 1
				if counter > 10:
					self.logging.logapimethoderror("getLastID", counter)
				time.sleep(1)
				continue


# ------------
# Testy:
# ------------

if __name__ == "__main__":

	def mezera():
		print("-" * 240)


	def clean():
		print("\n" * 70)


	clean()

	pla = PublicApi()
	tick = pla.getPublicParam("ticker", "btc_usd")

	pairs = pla.pairsFromDatabase()
	tickall = pla.tickerAllPairs()
	pairsinfo = pla.getPublicInfo()

	last = pla.getLast("btc_usd")
	lastID = pla.getLastID("btc_usd")

	mezera()
	print("Souhrnné informace o párech:")
	print(pairsinfo, "\n")

	mezera()
	print("Ticker pro btc_usd:")
	print(tick, "\n")

	mezera()
	print("Páry:")
	print(pairs, "\n")

	mezera()
	print("Ticker pro všechny páry:")
	print(tickall, "\n")

	mezera()
	print("Nejaktuálnější cena pro btc_usd:")
	print(last, "\n")

	mezera()
	print("ID posledního obchodu pro btc_usd:")
	print(lastID, "\n")
