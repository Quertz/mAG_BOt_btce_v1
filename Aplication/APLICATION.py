#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import sys
import os
import copy
import signal
import sqlite3
import subprocess
import time


# Přidání dočasných cest do $PYTHONPATH
# Seznam složek pro přidání do $PYTHONPATH generujeme v okamžiku spuštění programu, bez složky s databázemi a temporary.
directories = [d for d in os.listdir(os.getcwd()) if os.path.isdir(d) and d != "0_databases" and d != "0_temporary"]
# Výchozí složka
rootdir = os.getcwd()
# Přidání všech podsložek.
for i in directories:
	os.chdir(i)
	d = os.getcwd()
	sys.path.insert(0, d)
	os.chdir(rootdir)

import Logger
import Mailer
import Printer
import Api
import Helper
import DataConsistence


# ------------
# Konstanty
# ------------


PAIRSDATABASE = "./0_databases/pairsinfo.db"
CANDLESDATABASE = "./0_databases/candles.db"
INDICATORSDATABASE = "./0_databases/indicators.db"
SIGNALSDATABASE = "./0_databases/signals.db"
TICKERSDATABASE = "./0_databases/tickers.db"
TRADEPERMISSIONSFILE = "./0_temporary/tradespermissions.per"
COUNTERSRESETFILE = "./0_temporary/countersresetfile.per"


# ------------
# Třídy
# ------------

class LoadTables:
	"""
	Tato třída naplní postavené 'tables' daty z Btc-e a vytvoří
	candlesticky.
	"""

	def __init__(self):
		self.conf = Helper.Config()
		self.printer = Printer.AplicationPrinter()
		self.bigtickerfreq = self.conf.bigtickerfreq
		self.candlestickLenght = self.conf.candlestickLenght
		self.tradingStart = self.conf.overalldatalenght
		self.candle_ID = 1
		self.alltickersbiglist = []
		self.datacollectingprinter = Printer.DataCollectingPrinter()
		self.checkconsistence = DataConsistence.CheckConsistence()
		self.decisionspid = None
		self.closes = {}
		self.bigbud2keep = []

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

	def fetchAndFormatBigTickerData(self):
		"""
		Stáhne a formátuje velký ticker z funkce
		downloadTickerAllPairs(), do seznamu správně upravených
		slovníků.
		:return:
		"""

		def downloadTickerAllPairs():
			"""
			Stáhne tickery pro všechny páry z btc-e. K tomu využívá
			modul api.py.
			:return list:
			"""
			# Implementovat obchodování s jen některými páry.
			pairs = self.pairsFromDatabase()
			allstring = "-".join(pairs)
			get = Api.PublicApi()
			allpairsticker = get.getPublicParam("ticker", allstring)
			return allpairsticker

		def saveticker(ticker):
			con = sqlite3.connect(TICKERSDATABASE)
			cur = con.cursor()
			for key, value in ticker.items():
				cur.execute("DELETE FROM tickers_" + key)
				stringquery = 'INSERT INTO tickers_' + key + ' (high,low,sell,buy,avg,last,vol,vol_cur'\
				                                             ')' + ' VALUES(?,?,?,?,?,?,?,?)'
				val = (value["high"],
				       value["low"],
				       value["sell"],
				       value["buy"],
				       value["avg"],
				       value["last"],
				       value["vol"],
				       value["vol_cur"]
				       )
				cur.execute(stringquery, val)
				con.commit()
			con.close()

		dictbigticker = downloadTickerAllPairs()
		# Nyní převedu ticker do slovníku, poté jej převedu do databáze a iteruju až do konce posloupnosti.
		if dictbigticker:
			saveticker(dictbigticker)
			alltickers = []
			while True:
				for key, value in dictbigticker.items():
					newdict = {
						"pair": key,
						"high": value["high"],
						"low": value["low"],
						"avg": value["avg"],
						"last": value["last"],
						"sell": value["sell"],
						"buy": value["buy"],
						"vol": value["vol"],
						"vol_cur": value["vol_cur"]
					}
					alltickers.append(newdict)
				return alltickers
		else:
			return []

	def filllistswithformateddata(self, counter):
		"""
		Naformátuje data a nahraje je do seznamu v paměti.
		:param counter:
		:return bool:
		"""
		data = self.fetchAndFormatBigTickerData()
		# Pokud self.fetchAndFormatBigTickerData() navrátí data.
		if data:
			# Pokud counter signalizuje začátek sběru informací (== 1).
			if counter == 1:
				self.alltickersbiglist = []
				for i in data:
					curr_avg = (i["sell"] + i["buy"]) / 2
					nextdict = {}
					nextdict["pair"] = str()
					nextdict["high"] = list()
					nextdict["low"] = list()
					nextdict["avg"] = list()
					nextdict["last"] = list()
					nextdict["sell"] = list()
					nextdict["buy"] = list()
					nextdict["curr_avg"] = list()
					nextdict["vol"] = list()
					nextdict["vol_cur"] = list()

					nextdict["pair"] = i["pair"]
					nextdict["high"].append(i["high"])
					nextdict["low"].append(i["low"])
					nextdict["avg"].append(i["avg"])
					nextdict["last"].append(i["last"])
					nextdict["sell"].append(i["sell"])
					nextdict["buy"].append(i["buy"])
					nextdict["curr_avg"].append(curr_avg)
					nextdict["vol"].append(i["vol"])
					nextdict["vol_cur"].append(i["vol_cur"])
					self.alltickersbiglist.append(nextdict)
			# Pokud counter signalizuje pokračování sběru informací.
			elif counter > 1:
				for i in data:
					curr_avg = (i["sell"] + i["buy"]) / 2
					for n in self.alltickersbiglist:
						if i["pair"] == n["pair"]:
							n["high"].append(i["high"])
							n["low"].append(i["low"])
							n["avg"].append(i["avg"])
							n["last"].append(i["last"])
							n["sell"].append(i["sell"])
							n["buy"].append(i["buy"])
							n["curr_avg"].append(curr_avg)
							n["vol"].append(i["vol"])
							n["vol_cur"].append(i["vol_cur"])
		# Pokud self.fetchAndFormatBigTickerData() nenavrátí data.
		else:
			# Pokud counter signalizuje začátek sběru informací.
			if counter == 1:
				self.alltickersbiglist = []
				for i in self.pairsFromDatabase():
					nextdict = {}
					nextdict["pair"] = str()
					nextdict["high"] = list()
					nextdict["low"] = list()
					nextdict["avg"] = list()
					nextdict["last"] = list()
					nextdict["sell"] = list()
					nextdict["buy"] = list()
					nextdict["curr_avg"] = list()
					nextdict["vol"] = list()
					nextdict["vol_cur"] = list()
					nextdict["pair"] = i
					self.alltickersbiglist.append(nextdict)
			# Pokud counter signalizuje pokračování sběru informací.
			elif counter > 1:
				for i in self.pairsFromDatabase():
					for n in self.alltickersbiglist:
						if i == n["pair"]:
							pass

	def countData(self):
		"""
		Výpočetní úkony jsou implementovány zde.
		Tato funkce z tickerů v databázi vypočítá průměry,
		maxima, minima atd.
		:return list:
		"""
		# Kopíruju
		data = copy.deepcopy(self.alltickersbiglist)
		# Ihned mažu data.
		self.alltickersbiglist = []
		candlestickdata = []
		if data:
			for key in data:
				o = None
				c = None
				if key["curr_avg"]:
					fullpricerange = []
					fullpricerange += key["sell"]
					fullpricerange += key["buy"]
					fullpricerange += key["curr_avg"]
					if (int(self.candlestickLenght) / 60) > 1:
						delitel = int(self.candlestickLenght / 60)
						cut = int((len(key["curr_avg"]) / delitel) / 2)
						o = sum(key["curr_avg"][:cut]) / len(key["curr_avg"][:cut])
						c = sum(key["curr_avg"][-cut:]) / len(key["curr_avg"][-cut:])
					else:
						o = key["curr_avg"][0]
						c = key["curr_avg"][-1]
					pairdict = {
						"pair": key["pair"],
						"candle_ID": self.candle_ID,
						"time": time.asctime(),
						"open": o,
						"close": c,
						"min": min(fullpricerange),
						"max": max(fullpricerange),
						"avg": round(sum(key["curr_avg"]) / len(key["curr_avg"]), 12),
						# Jediným schůdným propočtem pro volumy se zdá být sečíst jejich průměr.
						"vol": round(sum(key["vol"]) / len(key["vol"]), 12),
						"vol_cur": round(sum(key["vol_cur"]) / len(key["vol_cur"]), 12)
					}
					candlestickdata.append(pairdict)
			return candlestickdata
		else:
			return candlestickdata

	def buildCandles(self):
		"""
		Postaví candlesticky v databázi z připravených a naformátovaných dat.
		:return None:
		"""
		bigbud = self.countData()
		con = sqlite3.connect(CANDLESDATABASE)
		cur = con.cursor()
		if bigbud:
			for pairdict in bigbud:
				if pairdict["avg"]:
					stringquery = 'INSERT INTO candlesticks_' + pairdict[
						"pair"] + ' (candle_ID, status, time, open, close,'\
					              'min, max, avg, vol, vol_currency'\
					              ')' + ' VALUES(?,?,?,?,?,?,?,?,?,?)'
					val = (pairdict["candle_ID"],
					       "real",
					       pairdict["time"],
					       pairdict["open"],
					       pairdict["close"],
					       pairdict["min"],
					       pairdict["max"],
					       pairdict["avg"],
					       pairdict["vol"],
					       pairdict["vol_cur"],
					       )
					cur.execute(stringquery, val)
					con.commit()
			con.close()
			self.checkconsistence.missingcandlescounter -= 1
			self.checkconsistence.checkconsistence()
			self.candle_ID += 1
			self.bigbud2keep = bigbud
		else:
			# Pokud už jsme obdrželi nějaká data:
			if self.bigbud2keep:
				for pairdict in self.bigbud2keep:
					if pairdict["avg"]:
						stringquery = 'INSERT INTO candlesticks_' + pairdict[
							"pair"] + ' (candle_ID, status, time, open, close,'\
						              'min, max, avg, vol, vol_currency'\
						              ')' + ' VALUES(?,?,?,?,?,?,?,?,?,?)'
						val = (int(self.candle_ID),
						       "false",
						       time.asctime(),
						       pairdict["open"],
						       pairdict["close"],
						       pairdict["min"],
						       pairdict["max"],
						       pairdict["avg"],
						       float(0.0),
						       float(0.0),
						       )
						cur.execute(stringquery, val)
						con.commit()
				con.close()
				self.candle_ID += 1
				self.checkconsistence.missingcandlescounter += 1
				self.checkconsistence.checkconsistence()
			else:
				# Pouze pro případ, že by došlo k výpadku spojení ihned po zapnutí
				# a my bychom neměli v cache žádná data.
				self.checkconsistence.missingcandlescounter += 1
				self.checkconsistence.checkconsistence()

	def candlesticksLopp(self):
		"""
		Povede smyčku pro naplnění databáze tickerů
		a spustí modul bookmaker.py, pokud máme
		požadovanou délku dat.
		:return:
		"""
		# Proměnné:
		tradinghasstarted = False
		now = int(time.time())
		nextcandle = int(now + self.candlestickLenght)

		# Funkce:
		def runDecisionsLoop():
			"""
			Spouští podproces modulu 'bookmaker.py'.
			:return:
			"""
			child = os.path.join(os.path.dirname(__file__),
			                     "DECISIONS.py")
			command = [sys.executable, child]
			proc = subprocess.Popen(command)
			self.decisionspid = proc.pid

		# TĚLO:
		while True:
			counter = 1
			while int(time.time()) <= (nextcandle - self.bigtickerfreq):
				self.filllistswithformateddata(counter)
				counter += 1
				time.sleep(int(self.bigtickerfreq))
				continue
			self.buildCandles()
			now = int(time.time())
			nextcandle = int(now + self.candlestickLenght)

			if self.conf.datacollecting:
				self.datacollectingprinter.printDataColecting(self.candlestickLenght,
				                                              self.bigtickerfreq,
				                                              int(self.candle_ID - 1))
			else:
				pass

			if self.candle_ID == (self.tradingStart + 1):
				if not tradinghasstarted:
					if not self.conf.datacollecting:
						self.printer.starttradingsignalsloading()
						runDecisionsLoop()
						tradinghasstarted = True
					else:
						pass
				else:
					pass
			else:
				pass

			continue


class mAG_BOt:
	"""
	Hlavní instance bota.
	"""

	def __init__(self):
		"""
		Inicializace proměnných třídy.
		:return:
		"""
		self.config = Helper.Config()
		self.lt = LoadTables()
		self.subproc1_pid = None
		self.subproc2_pid = None
		self.subproc3a_pid = None
		self.logger = Logger.AplicationLogging()
		self.printer = Printer.AplicationPrinter()
		self.mailer = Mailer.Mailer()
		self.checkconsistence = DataConsistence.CheckConsistence()

	def runOnce(self):
		"""
		Zavolá funkce které připraví prostředí pro běh programu.
		Tato metoda obsahuje funkce, které se spustí jen jednou
		na začátku běhu programu.
		:return:
		"""
		self.printer.printwelcome()

		def changeRightsONBegin():
			"""
			Na začátku běhu aplikace změní,
			práva přístupu k souborům.
			"""
			subprocess.call("../bash_scripts/harden_start.sh")

		def buildTables():
			"""
			Postaví databáze pro běh programu.
			:return:
			"""
			child = os.path.join(os.path.dirname(__file__),
			                     "./SideModules/Databases.py")
			command = [sys.executable, child]
			pipe = subprocess.Popen(command)
			pipe.wait()

		def makecountersresetfile():
			fobj = open(COUNTERSRESETFILE, "w", encoding="UTF-8")
			fobj.write("False")
			fobj.close()

		changeRightsONBegin()
		time.sleep(1)
		buildTables()
		time.sleep(1)
		makecountersresetfile()
		# Zaloguje začátek běhu programu.
		self.logger.logAplicationStart()
		# Pošle email o startu bota.
		if self.config.sendMails:
			self.mailer.reportBotBegins()
		self.checkconsistence.denyTrades()

	def runLopps(self):
		self.printer.printReady()
		self.lt.candlesticksLopp()

	def main(self):
		"""
		Rozběhne všechny třídy a celého bota.
		:return:
		"""

		def changeRightsONEnd():
			"""
			Na konci běhu aplikace navrací,
			práva přístupu k souborům.
			"""
			subprocess.call("../bash_scripts/harden_stop.sh")

		try:
			self.runOnce()
			if self.config.apikey and self.config.secret:
				self.runLopps()
			elif not self.config.apikey or not self.config.secret:
				if self.config.datacollecting or self.config.simMode:
					self.runLopps()
				else:
					self.printer.printkeysmissing()
		except KeyboardInterrupt:
			self.printer.printKill()

		finally:
			# Zalogguje konec programu
			self.logger.logAplicationEnd()
			# Pošle email.
			if self.config.sendMails:
				self.mailer.reportBotEnded()
			changeRightsONEnd()

			# Funkce zabití procesů
			def kill_child(child_pid):
				if child_pid is None:
					pass
				else:
					os.kill(child_pid, signal.SIGTERM)

			self.subproc1_pid = self.lt.decisionspid
			subprocpids = (self.subproc1_pid,)
			for i in subprocpids:
				kill_child(i)


if __name__ == "__main__":
	mb = mAG_BOt()
	mb.main()
