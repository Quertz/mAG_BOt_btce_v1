#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import sqlite3
import time
import os
import sys


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

import Helper
import Printer
import Indicators
import ProceedAlgorythms
import Logger
import DataConsistence
import PricePolicy


"""
Tento modul načte data candlesticků, naformátuje je
a postaví databáze oscilátorů. Pokud data dosahují
potřebné délky, vyvolá obchody.
Dále načte data z databází oscilátorů
a vyhodnotí je na základě algorytmů sestavenývh
pro nákup a prodej.Toto je jádro pro obchodování.
"""

# ------------
# Konstanty
# ------------

PAIRSDATABASE = "./0_databases/pairsinfo.db"
CANDLESDATABASE = "./0_databases/candles.db"
INDICATORSDATABASE = "./0_databases/indicators.db"
SIGNALSDATABASE = "./0_databases/signals.db"
TICKERSDATABASE = "./0_databases/tickers.db"
TRADEPERMISSIONSFILE = "./0_temporary/tradespermissions.per"
FETCHDATALENGTH = 10


# ------------
# Třídy
# ------------

class FillIndicators:
	"""
	Tato třída načte data candlesticků a
	naformátuje jejich posloupnost.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.tradedatalength = self.config.overalldatalenght
		self.indicators = Indicators.TradingIndicators()
		self.printer = Printer.AplicationPrinter()

	def pairsFromDatabase(self):
		"""
		Vyzíská páry z databáze, kam jsme je umístili abychom co nejméně
		zatěžovali servery z btc-e.
		:return set:
		"""
		con = sqlite3.connect(PAIRSDATABASE)
		cur = con.cursor()
		pairs = []
		for pair in cur.execute("SELECT * FROM pairs"):
			pairs.append(pair[0])
		con.close()
		# Unique
		return set(pairs)

	def fetchData(self):
		con = sqlite3.connect(CANDLESDATABASE)
		cur = con.cursor()
		bigdata = []
		for pair in self.pairsFromDatabase():
			newdict = {
				"pair": pair,
				"length": [],
				"statuses": [],
				"opens": [],
				"closes": [],
				"minima": [],
				"maxima": [],
				"averages": [],
				"volumes": [],
				"volumes_currency": []
			}
			for i in cur.execute("SELECT * FROM candlesticks_" + pair):
				newdict["length"].append(i[0])
				newdict["statuses"].append(i[1])
				newdict["opens"].append(i[3])
				newdict["closes"].append(i[4])
				newdict["minima"].append(i[5])
				newdict["maxima"].append(i[6])
				newdict["averages"].append(i[7])
				newdict["volumes"].append(i[8])
				newdict["volumes_currency"].append(i[9])
			bigdata.append(newdict)
		con.close()
		return bigdata

	def cutLength(self):
		"""
		Tato funkce zajistí správnou délku
		a naformátování dat pro oscilátory.
		Tato posloupnost bude prezentována
		modulu oscilators.py jako jeho dataset.
		Moohlo by se to celé nechat na tom modulu
		a posílat mu plnou délku dat, ale je lepší
		data předformátovat, aby modul oscilators.py
		nemusel pracovat s plnou, dlouhou, posloupností
		dat.
		:return list:
		"""
		bigdata = []
		for dat in self.fetchData():
			# Pokud je posloupnost kratší, než její požadovaná délka,
			# jen označíma aktivaci obchodů za nepravdu.
			if len(dat["length"]) < self.tradedatalength:
				# Vyprázdníme seznam dat, abychom mohli v dalším kroku úspěšně provést kontrolu.
				self.printer.printshortcandleserror()
				pass
			# Pokud je posloupnost delší, než její požadovaná délka,
			# posloupnost zkrátíme.
			elif len(dat["length"]) >= self.tradedatalength:
				# Syrová data převedena do n-tice.
				# Určíme počátek řezu.
				# Data jsou srovnána od nejstaršího po nejaktuálnější.
				cutbegin = len(dat["length"]) - self.tradedatalength
				nextdict = {
					"pair": dat["pair"],
					"opens": dat["opens"][cutbegin:],
					"closes": dat["closes"][cutbegin:],
					"lows": dat["minima"][cutbegin:],
					"highs": dat["maxima"][cutbegin:],
					"averages": dat["averages"][cutbegin:],
					"volumes": dat["volumes"][cutbegin:],
					"volumes_currency": dat["volumes_currency"][cutbegin:]
				}
				bigdata.append(nextdict)
		return list(bigdata)

	def fillIndicators(self):
		"""
		Naplní databáze indikátorů vypočítanými daty.
		:return boolean:
		"""
		data = self.cutLength()
		con = sqlite3.connect(INDICATORSDATABASE)
		cur = con.cursor()
		for i in data:
			trima = self.indicators.trima(i["averages"])
			macd = self.indicators.macd(i["averages"])
			stochastic = self.indicators.stochastic(i["highs"], i["lows"], i["closes"])
			newdict = {
				"pair": i["pair"],
				"price": i["averages"][-1],
				"natr": self.indicators.natr(i["highs"], i["lows"], i["closes"]),
				"rsi": self.indicators.rsi(i["averages"]),
				"stoch_k": stochastic[0],
				"stoch_d": stochastic[1],
				"macd": float(macd[0]),
				"macdsignal": float(macd[1]),
				"macdhistogram": float(macd[2]),
				"trimaultrafast": float(trima[0]),
				"trimafast": float(trima[1]),
				"trimaslow": float(trima[2]),
				"ad": self.indicators.ad(i["highs"], i["lows"], i["closes"],
				                         i["volumes"]),
				"bop": self.indicators.bop(i["opens"], i["highs"], i["lows"],
				                           i["closes"]),
				"mom": self.indicators.mom(i["averages"])
			}
			stringquery = 'INSERT INTO signals_' + newdict["pair"] + '(avg_price, NATR, RSI, STOCH_K, '\
			                                                         'STOCH_D,'\
			                                                         ' MACD, MACDsign, MACDhist,'\
			                                                         ' TRIMAultrafast, TRIMAfast, TRIMAslow,'\
			                                                         ' AD, BOP, MOM'\
			                                                         ')' + ' VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'\
			                                                               '?,?)'
			val = [newdict["price"], newdict["natr"], newdict["rsi"], newdict["stoch_k"], newdict["stoch_d"],
			       newdict["macd"], newdict["macdsignal"], newdict["macdhistogram"],
			       newdict["trimaultrafast"], newdict["trimafast"], newdict["trimaslow"],
			       newdict["ad"], newdict["bop"], newdict["mom"]
			       ]
			cur.execute(stringquery, val)
		con.commit()
		con.close()


class FillSignals:
	"""
	Tato třída načte data candlesticků a
	naformátuje jejich posloupnost.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.indicatorslength = self.config.indicatorsLength
		self.indicators = Indicators.TradingIndicators()

	def pairsFromDatabase(self):
		"""
		Vyzíská páry z databáze, kam jsme je umístili abychom co nejméně
		zatěžovali servery z btc-e.
		:return set:
		"""
		con = sqlite3.connect(PAIRSDATABASE)
		cur = con.cursor()
		pairs = []
		for pair in cur.execute("SELECT * FROM pairs"):
			pairs.append(pair[0])
		con.close()
		# Unique
		return set(pairs)

	def fetchData(self):
		scon = sqlite3.connect(INDICATORSDATABASE)
		scur = scon.cursor()
		bigdata = []
		pairs = self.pairsFromDatabase()
		for pair in pairs:
			newdict = {
				"pair": pair,
				"rsi": [],
				"macd": [],
				"stoch_k": [],
				"trimaultrafast": [],
				"ad": [],
				"bop": [],
				"natr": [],
				"mom": []
			}
			for i in scur.execute("SELECT * FROM signals_" + pair):
				newdict["rsi"].append(i[2])
				newdict["stoch_k"].append(i[3])
				newdict["macd"].append(i[6])
				newdict["trimaultrafast"].append(i[8])
				newdict["ad"].append(i[11])
				newdict["bop"].append(i[12])
				newdict["natr"].append(i[1])
				newdict["mom"].append(i[13])
			bigdata.append(newdict)
		scon.close()
		return bigdata

	def cutLength(self):
		"""
		Tato funkce zajistí správnou délku
		a naformátování dat pro oscilátory.
		Tato posloupnost bude prezentována
		modulu oscilators.py jako jeho dataset.
		Moohlo by se to celé nechat na tom modulu
		a posílat mu plnou délku dat, ale je lepší
		data předformátovat, aby modul oscilators.py
		nemusel pracovat s plnou, dlouhou, posloupností
		dat.
		:return list:
		"""
		resultdata = []
		bigdata = self.fetchData()
		for dat in bigdata:
			if len(dat["rsi"]) < self.indicatorslength:
				self.printer.printshortemacandleserror()
				break
			else:
				cutbegin = - int(self.indicatorslength)
				nextdict = {
					"pair": dat["pair"],
					"rsi": dat["rsi"][cutbegin:],
					"macd": dat["macd"][cutbegin:],
					"stoch_k": dat["stoch_k"][cutbegin:],
					"trimaultrafast": dat["trimaultrafast"][cutbegin:],
					"ad": dat["ad"][cutbegin:],
					"bop": dat["bop"][cutbegin:],
					"natr": dat["natr"][cutbegin:],
					"mom": dat["mom"][cutbegin:]
				}
				resultdata.append(nextdict)
		return resultdata

	def fillSignals(self):
		"""
		Naplní databáze indikátorů vypočítanými daty.
		:return boolean:
		"""
		data = self.cutLength()
		con = sqlite3.connect(SIGNALSDATABASE)
		cur = con.cursor()
		for nextdict in data:
			rsi = self.indicators.indicatorsTrima(nextdict["rsi"], self.config.rsiEmaSlow)
			macd = self.indicators.indicatorsTrima(nextdict["macd"], self.config.macdEmaSlow)
			stoch = self.indicators.indicatorsTrima(nextdict["stoch_k"], self.config.stochasticEmaSlow)
			trimaultraslow = self.indicators.indicatorsTrima(nextdict["trimaultrafast"], self.config.indicatorsLength)
			ad = self.indicators.indicatorsTrima(nextdict["ad"], self.config.adEmaSlow)
			bop = self.indicators.indicatorsTrima(nextdict["bop"], self.config.bopEmaSlow)
			natr = self.indicators.indicatorsTrima(nextdict["natr"], self.config.natrEmaSlow)
			mom = self.indicators.indicatorsTrima(nextdict["mom"], self.config.momEmaSlow)
			newdict = {
				"pair": nextdict["pair"],
				"rsiema": float(rsi),
				"macdema": float(macd),
				"stochasticema": float(stoch),
				"trimaultraslow": float(trimaultraslow),
				"adema": float(ad),
				"bopema": float(bop),
				"natrema": float(natr),
				"momema": float(mom)
			}
			stringquery = 'INSERT INTO signals_' + newdict[
				"pair"] + '(RSIema, MACDema, STOCHema, TRIMAultraslow, ADema, BOPema, NATRema, Momema)' + ' VALUES(?,'\
			                                                                                              '?,?,?,?,'\
			                                                                                              '?,?,?)'
			val = [newdict["rsiema"], newdict["macdema"], newdict["stochasticema"], newdict["trimaultraslow"],
			       newdict["adema"], newdict["bopema"], newdict["natrema"], newdict["momema"]]
			cur.execute(stringquery, val)
		con.commit()
		con.close()


class FetchDataForDecisions:
	"""
	Tato třída načte data candlesticků a
	naformátuje jejich posloupnost.
	Nepoužíváme pokud nejedeme reállná data.
	"""

	def __init__(self):
		self.config = Helper.Config()

	def pairsFromDatabase(self):
		"""
		Vyzíská páry z databáze, kam jsme je umístili abychom co nejméně
		zatěžovali servery z btc-e.
		:return set:
		"""
		con = sqlite3.connect(PAIRSDATABASE)
		cur = con.cursor()
		pairs = []
		for pair in cur.execute("SELECT * FROM pairs"):
			pairs.append(pair[0])
		con.close()
		# Unique
		return set(pairs)

	def fetchData(self):
		"""
		Vyzíská data z databáze indikátorů, přiřadí je do slovníků a
		vystřihne správnou délku. Projede databáze všech indikátorů a
		navrátí je ve velkém seznamu.
		:return:
		"""
		con = sqlite3.connect(CANDLESDATABASE)
		cur = con.cursor()
		icon = sqlite3.connect(INDICATORSDATABASE)
		icur = icon.cursor()
		scon = sqlite3.connect(SIGNALSDATABASE)
		scur = scon.cursor()
		bigdata = []
		pairs = tuple(self.pairsFromDatabase())
		for pair in pairs:
			nextdict = {}
			newdict = {
				# Názvy z databáze indikátorů.
				"natr": [],
				"rsi": [],
				"stoch_k": [],
				"stoch_d": [],
				"macd": [],
				"macdsignal": [],
				"macdhistogram": [],
				"trimaultrafast": [],
				"trimafast": [],
				"trimaslow": [],
				"ad": [],
				"bop": [],
				"mom": [],
				# Názvy z databáze candlesticků.
				"pair": pair,
				"length": [],
				"statuses": [],
				"opens": [],
				"closes": [],
				"minima": [],
				"maxima": [],
				"avg_price": [],
				"volumes": [],
				"volumes_currency": [],
				# Názvy z databáze signálů.
				"rsiema": [],
				"macdema": [],
				"stochema": [],
				"trimaultraslow": [],
				"adema": [],
				"bopema": [],
				"natrema": [],
				"momema": []
			}

			for i in cur.execute("SELECT * FROM candlesticks_" + pair):
				# Hodnoty z databáze candlesticků.
				newdict["opens"].append(i[3])
				newdict["closes"].append(i[4])
				newdict["minima"].append(i[5])
				newdict["maxima"].append(i[6])
				newdict["avg_price"].append(i[7])
				newdict["volumes"].append(i[8])
				newdict["volumes_currency"].append(i[9])

			for i in icur.execute("SELECT * FROM signals_" + pair):
				newdict["length"].append(i[0])
				newdict["natr"].append(i[1])
				newdict["rsi"].append(i[2])
				newdict["stoch_k"].append(i[3])
				newdict["stoch_d"].append(i[4])
				newdict["macd"].append(i[5])
				newdict["macdsignal"].append(i[6])
				newdict["macdhistogram"].append(i[7])
				newdict["trimaultrafast"].append(i[8])
				newdict["trimafast"].append(i[9])
				newdict["trimaslow"].append(i[10])
				newdict["ad"].append(i[11])
				newdict["bop"].append(i[12])
				newdict["mom"].append(i[13])

			for i in scur.execute("SELECT * FROM signals_" + pair):
				newdict["rsiema"].append(i[0])
				newdict["macdema"].append(i[1])
				newdict["stochema"].append(i[2])
				newdict["trimaultraslow"].append(i[3])
				newdict["adema"].append(i[4])
				newdict["bopema"].append(i[5])
				newdict["natrema"].append(i[6])
				newdict["momema"].append(i[7])

				# Nastříháme posloupnosti ve slovnících:
				# Délku výřezu určujeme z nějakého indikátoru, protože
				# indikátory jsou kratší, než candlesticky.
				cutlength = FETCHDATALENGTH
				# Naiterujeme od 1 novou délku.
				# Pro jistotu o něco delší, později ji také seřízneme.
				newlength = [x for x in range(1, cutlength + 1)]
				# candlesticky
				nextdict["pair"] = newdict["pair"]
				nextdict["length"] = newlength[-cutlength:]
				nextdict["opens"] = newdict["opens"][-cutlength:]
				nextdict["closes"] = newdict["closes"][-cutlength:]
				nextdict["minima"] = newdict["minima"][-cutlength:]
				nextdict["maxima"] = newdict["maxima"][-cutlength:]
				nextdict["avg_price"] = newdict["avg_price"][-cutlength:]
				nextdict["volumes"] = newdict["volumes"][-cutlength:]
				nextdict["volumes_currency"] = newdict["volumes_currency"][-cutlength:]
				# indikátory
				nextdict["natr"] = newdict["natr"][-cutlength:]
				nextdict["rsi"] = newdict["rsi"][-cutlength:]
				nextdict["stoch_k"] = newdict["stoch_k"][-cutlength:]
				nextdict["stoch_d"] = newdict["stoch_d"][-cutlength:]
				nextdict["macd"] = newdict["macd"][-cutlength:]
				nextdict["macdsignal"] = newdict["macdsignal"][-cutlength:]
				nextdict["macdhistogram"] = newdict["macdhistogram"][-cutlength:]
				nextdict["trimaultrafast"] = newdict["trimaultrafast"][-cutlength:]
				nextdict["trimafast"] = newdict["trimafast"][-cutlength:]
				nextdict["trimaslow"] = newdict["trimaslow"][-cutlength:]
				nextdict["ad"] = newdict["ad"][-cutlength:]
				nextdict["bop"] = newdict["bop"][-cutlength:]
				nextdict["mom"] = newdict["mom"][-cutlength:]
				nextdict["trimaultraslow"] = newdict["trimaultraslow"][-cutlength:]
				# signály
				nextdict["rsiema"] = newdict["rsiema"][-cutlength:]
				nextdict["macdema"] = newdict["macdema"][-cutlength:]
				nextdict["stochema"] = newdict["stochema"][-cutlength:]
				nextdict["trimaultraslow"] = newdict["trimaultraslow"][-cutlength:]
				nextdict["adema"] = newdict["adema"][-cutlength:]
				nextdict["bopema"] = newdict["bopema"][-cutlength:]
				nextdict["natrema"] = newdict["natrema"][-cutlength:]
				nextdict["momema"] = newdict["momema"][-cutlength:]

			bigdata.append(nextdict)
		con.close()
		icon.close()
		scon.close()
		return bigdata


class GetBothListsAndTrade:
	"""
	Tato třída navrátí seznamy pro nákup
	i prodej. Kontroluje zdroj dat pro
	vyhodnocování a skrze tuto třídu se
	ovládají třídy 'BuyDecisions' a
	'SellDecisions'.
	"""

	def __init__(self):
		"""
		Inicializuje moduly k rozhodnutí
		o nákupu či prodeji, a simulaci,
		či ostré obchodování.
		:return:
		"""
		self.config = Helper.Config()
		self.logger = Logger.TraderLogging()
		self.simmode = self.config.simMode
		self.tradedecisions = ProceedAlgorythms.AllDecisionsAndStrategies()
		self.fetch = FetchDataForDecisions()
		self.tradingpairs = self.fetch.pairsFromDatabase()
		# self.realtimepricepolicy = PricePolicy.RealtimePricePolicy()
		self.boughts = []
		if self.simmode:
			import Simulation
			self.trade = Simulation.Trade()
		else:
			import Trader
			self.trade = Trader.Trade()

	def getAll(self):
		"""
		Dostane informace z modulu
		ProceedAlgorythms.py o párech
		k prodeji.
		:return:
		"""
		tradeslist = None
		bigdataset = self.fetch.fetchData()
		# Zde jsem musel dát self.boughts jako druhý argument, kvůli price policy.
		tradeslist = self.tradedecisions.applyAll(bigdataset, self.tradingpairs, self.boughts)
		buys = tradeslist[0]
		sells = tradeslist[1]
		if sells:
			self.logger.logsellrecommandations(sells)
		if buys:
			self.logger.logbuyrecommandations(buys)
		# Návrat pro nákup:
		# [{'price': 575.952678041544, 'algorythm': 1, 'pair': 'btc_usd', 'sequencialbuy': 5},]
		# Návrat pro prodej:
		# [{'algorythm': 1, 'pair': 'btc_usd'},]
		return tradeslist

	def control(self):
		lists = self.getAll()
		buylist = lists[0]
		selllist = lists[1]
		self.boughts = self.trade.controlTrades(sells=selllist, buys=buylist)

	# def applyRealtimePricePolicy(self):
	# """
	# Aplikujeme RealTimePricePolicy.
	# """
	# sells = []
	# if self.boughts:
	# sells = self.realtimepricepolicy.proceedprices(self.boughts)
	# if sells:
	# self.boughts = self.trade.controlTrades(sells=sells, buys=[])


class BigCyklus:
	"""
	Tato třída vytváří velký cyklus
	nákupů. Plní databáze indikátorů,
	vyvolává decisions i nákupy.
	"""

	def __init__(self):
		self.fd = FillIndicators()
		self.fs = FillSignals()
		self.trade = GetBothListsAndTrade()
		self.checkconsistence = DataConsistence.CheckConsistence()
		self.config = Helper.Config()
		self.candlesticklength = self.config.candlestickLenght
		self.tickerfrequency = self.config.bigtickerfreq
		self.cyklescounter = 0
		self.trading = False

	def loop(self):
		# Při prvním cyklu se lehce vzdálím od cyklu pro stavbu candlesticků.
		nextcandle = int(time.time() + 2)
		nextrealtimecykle = int(time.time() + self.tickerfrequency)
		tradesstartpoint = int(self.config.indicatorsLength + FETCHDATALENGTH + 1)
		while True:
			# Cyklus toho co vše má být provedeno v cyklu jednoho candlesticku:
			if int(time.time()) >= nextcandle:
				nextcandle += int(self.candlesticklength)
				self.cyklescounter += 1
				self.fd.fillIndicators()
				if self.cyklescounter > int(self.config.indicatorsLength):
					self.fs.fillSignals()
					if self.cyklescounter == int(tradesstartpoint):
						self.checkconsistence.alowTrades()
						self.trading = True
					elif self.cyklescounter > int(tradesstartpoint):
						self.trade.control()
					else:
						continue
				continue
			# Cyklus jednoho tickeru:
			elif int(time.time()) >= nextrealtimecykle:
				nextrealtimecykle = int(time.time() + self.tickerfrequency)
			# if self.config.usePricePolicy and self.trading:
			# self.trade.applyRealtimePricePolicy()
			else:
				time.sleep(0.5)
			continue


def main():
	bc = BigCyklus()
	bc.loop()


main()
