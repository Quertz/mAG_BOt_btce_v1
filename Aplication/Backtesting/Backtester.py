#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import os
import sys
import time
import sqlite3
import shutil
import matplotlib
import matplotlib.pyplot as plt


# Na některých systémech není candlestick v matplotlib přítomen,
# ale je ve formě candlestick_ochl.
try:
	from matplotlib.finance import candlestick
except ImportError as e:
	from matplotlib.finance import candlestick_ochl as candlestick
from configparser import ConfigParser


# Nastaveni globalnich parametru pro matplotlib, font atd.
matplotlib.rcParams.update({'font.size': 8})

# Přidání dočasných cest do $PYTHONPATH
# Výchozí složka
homedir = os.getcwd()
os.chdir("..")
# Seznam složek generujeme v reálném čase, bez složky s databázemi.
directories = [d for d in os.listdir(os.getcwd()) if os.path.isdir(d) and d != "0_databases" and d != "0_temporary"]
rootdir = os.getcwd()
# Přidání všech podsložek.
for i in directories:
	os.chdir(i)
	d = os.getcwd()
	sys.path.insert(0, d)
	os.chdir(rootdir)

# Nenavracíme se do homedir ale zůstáváme v rootdirectory,
# kvůli importům helper atd..

import Helper
import Indicators
import Logger
import Printer
import ProceedAlgorythms
import Api


"""
Modul pro backtesting simuluje prostředí a čas trhu. K vyhodnocování
a rozhodování používá stejné moduly jako mag_bot. Backtesting můžeme
provádět v režimu testů pro jeden pár, chceme-li vyprofilovat a
odhalit povahu jednoho páru, anebo v režimu více párů, což spíše
odpovídá realitě, pokud obchodujeme více párů i ve skutečnosti. Ve
složce s nastavením jsou soubory pro nastavení backtestingu, pro
měny které chceme vynechat, při sestavování párů a páry k
obchodování, které můžeme ručně upravit.
Třídy:
Config4Backtesting(): Má na starosti veškeré nastavení backtestingu,
včetně dotazů pro uživatele. První dotaz se týká online či offline
backtestingu a druhý se týká sestavení nového seznamu párů.
BuildDatabases(): Postaví nejen databáze, ale i textové soubory s
páry, při jejichž sestavování, vynechá páry, jež obsahují nechtěné
měny. FetchDataForDecisions(): Načte data z databází. Obsahuje také
metodu, která z data vystříhává potřebné ůseky.
Backtesting() třída má na starost backtesting jako takový.
"""

# ------------
# Konstanty
# ------------

OLDBACKTESTINGPAIRSDATABASE = "./Backtesting/backtesting_databases/.persistant_databases/pairsinfo.db"
BACKTESTINGPAIRSDATABASE = "./Backtesting/backtesting_databases/pairsinfo.db"
BACKTESTINGCANDLESDATABASE = "./Backtesting/backtesting_databases/candles.db"
BACKTESTINGINDICATORSDATABASE = "./Backtesting/backtesting_databases/indicators.db"
BACKTESTINGSIGNALSDATABASE = "./Backtesting/backtesting_databases/signals.db"
BACKTESTERSETTINGSFILE = "./Backtesting/settings4backtests/backtestersett.ini"
PAIRS2TESTFILE = "./Backtesting/settings4backtests/pairs2test"
CURRENCIES2SKIPFILE = "./Backtesting/settings4backtests/currencies2skip"


# ------------
# Třídy
# ------------


class Config4Backtesting:
	"""
	Načte konfigurační soubor od uživatele a uchová zadané
	hodnoty v proměnných aplikace. Pokládá dotazy uživateli.
	"""

	def __init__(self):
		self.settingsfile = BACKTESTERSETTINGSFILE
		self.parser = ConfigParser()
		self.singlePairBacktest = None
		self.plotpair = None
		self.tradessimulation = None
		self.plotgraphs = None
		self.savegraphs = None
		self.online = None
		self.loadnewtradingpairs = None
		self.updateALL()

	def updateALL(self):
		"""
		Aktualizuj a uchovej uživatelská nastavení
		ze souboru.
		:return:
		"""
		self.parser.read(self.settingsfile)
		# Nastavení Settings pro backtesting.
		self.singlePairBacktest = self.parser.getboolean("Settings", "singlePairBacktest")
		self.plotpair = str(self.parser.get("Settings", "plotPair"))
		self.tradessimulation = self.parser.getboolean("Settings", "backtesting")
		self.plotgraphs = self.parser.getboolean("Settings", "graphs")
		self.savegraphs = self.parser.getboolean("Settings", "saveGraphs")

	def getAnswers(self):
		"""
		Metoda jež zastřešuje dotazy na uživatele.
		Po získání odpovědí, přistupujeme k jejich výsledkům
		pomocí přiřazených proměnných.
		:return:
		"""
		self.online = bool(self.getConnectionStatus())
		if self.online:
			if self.singlePairBacktest is False:
				self.loadnewtradingpairs = bool(self.loadNewTradingPairs())
			else:
				# Pokud jsme v módu testování jen jednoho páru,
				# nepotřebujeme nahrávat nové páry.
				self.loadnewtradingpairs = False
		else:
			self.loadnewtradingpairs = False

	def getConnectionStatus(self):
		"""
		Získá od uživatele odpověď na to, zda má provádět
		online či offline testy.
		"""
		answer = None
		s = None

		def clear_terminal():
			se = "\n"
			print(25 * se)

		clear_terminal()
		print(
			"ONLINE či OFFLINE MÓD?\n"
			"Při online módu se nahrají nové informace a \n"
			"můžete upravovat seznamy párů.\n"
			"Pro offline mód nepotřebujete internetové připojení.\n"
			"Pokud zmáčknete jen ENTER, použije se výchozí offline mód.\n\n"
		)
		while True:
			s = str(input("Zahájit online backtesting? (a/n nebo Enter) "))
			if s:
				if s == "a" or s == "A":
					answer = True
					break
				elif s == "n" or s == "N":
					answer = False
					break
				else:
					print("Odpověď musí být (a/n)!")
					continue
			else:
				answer = False
				break
		return answer

	def loadNewTradingPairs(self):
		"""
		Dotáže se, zda má sestavit nový seznam párů.
		Při jeho sestavování vynechá páry, které obsahují
		nechtěné měny.
		"""
		answer = None
		s = None

		def clear_terminal():
			se = "\n"
			print(25 * se)

		clear_terminal()
		print(
			"NOVÝ SEZNAM PÁRŮ?\n"
			"Můžu sestavit nový seznam párů a uložit jej do " +
			str(PAIRS2TESTFILE) +
			"\n"
			"Kde jej pak můžete upravit a vybrat páry jež opravdu chcete testovat.\n"
			"Při sestavování seznamu se vynechají páry, které obsahují měny v souboru " +
			CURRENCIES2SKIPFILE +
			".\n"
			"Výchozí stav je nesestavování nového seznamu."
			"Pokud zmáčknete jen ENTER, použije se výchozí stav.\n\n"
		)
		while True:
			s = str(input("Sestavit nový seznam párů? (a/n nebo Enter) "))
			if s:
				if s == "a" or s == "A":
					answer = True
					break
				elif s == "n" or s == "N":
					answer = False
					break
				else:
					print("Odpověď musí být (a/n)!")
					continue
			else:
				answer = False
				break
		return answer

	def wait4PairsAdjust(self):
		"""
		Čeká na ůpravu párů.
		:return:
		"""

		def clear_terminal():
			se = "\n"
			print(25 * se)

		clear_terminal()
		s = str(
			input(
				"Nyní můžete upravit páry v souboru " +
				str(PAIRS2TESTFILE) +
				".\n"
				"Až budete hotovi zmáčkněte ENTER."
			)
		)
		clear_terminal()
		print("Pokračuji se stavbou databází...")
		return True


class BuildDatabases:
	"""
	Tato třída načte data candlesticků,
	zkontroluje výši fejkových dat a
	naformátuje jejich posloupnost.
	Znovuzkonstruuje databáze oscilátorů
	na základě nastavení.
	"""

	def __init__(self):
		self.cleanDatabases()
		# Hlavní konfigurace.
		self.config = Helper.Config()
		self.tradedatalength = self.config.indicatorsLength
		self.candleslength = self.config.overalldatalenght
		# Inicializace konfigurace pro backtesting.
		self.backconfig = Config4Backtesting()
		self.singlePairBacktest = self.backconfig.singlePairBacktest
		self.testingpair = self.backconfig.plotpair
		# Dotazy na uživatele.
		self.backconfig.getAnswers()
		# Odpovědi od uživatele.
		self.online = self.backconfig.online
		self.loadnewtradingpairs = self.backconfig.loadnewtradingpairs
		self.indicators = Indicators.TradingIndicators()
		self.logger = Logger.BacktesterLogging()
		self.printer = Printer.BacktesterPrinter()
		self.alltestingpairs = tuple()

	def cleanDatabases(self):
		"""
		Odstraní staré databáze.
		:return:
		"""
		# Odstranění starých databází.
		try:
			os.remove(BACKTESTINGPAIRSDATABASE)
			os.remove(BACKTESTINGINDICATORSDATABASE)
			os.remove(BACKTESTINGSIGNALSDATABASE)
		except Exception as e:
			pass

	def buildPairsTable(self):
		"""
		Tato metoda vytvoří, či aktualizuje databázi měnových párů.
		:return:
		"""

		con = sqlite3.connect(BACKTESTINGPAIRSDATABASE)
		cur = con.cursor()

		def getPairsFullInfo():
			"""
			Získá aktuální obchodovatelné páry z btc-e.com pomocí modulu api.py
			a porovná je s páry, které chceme obchodovat v nastavení.
			Pokud je pár v obou skupinách, vytvoří pro něj řádek v databázi.
			"""
			get = Api.PublicApi()
			raw = dict(get.getPublicInfo())
			rawpairsinfo = raw["pairs"]
			pairsinfolist = []
			while True:
				for key, value in rawpairsinfo.items():
					pairdict = {
						"pair": key,
						"decimal": value["decimal_places"],
						"min_price": value["min_price"],
						"max_price": value["max_price"],
						"fee": value["fee"],
						"min_amount": value["min_amount"]
					}
					pairsinfolist.append(pairdict)
					continue
				return pairsinfolist

		cur.execute("CREATE TABLE IF NOT EXISTS pairs(pair,decimal,min_price,max_price,fee,min_amount )")
		con.commit()
		# Aktualizuj
		cur.execute("DELETE FROM pairs")
		for d in getPairsFullInfo():
			cur.execute("INSERT OR IGNORE INTO pairs VALUES(?,?,?,?,?,?)",
			            (d["pair"], d["decimal"], d["min_price"], d["max_price"], d["fee"],
			             d["min_amount"],))
		con.commit()
		con.close()
		# Novou databází aktualizujeme uchované databáze.
		if os.path.exists(OLDBACKTESTINGPAIRSDATABASE):
			os.remove(OLDBACKTESTINGPAIRSDATABASE)
		shutil.copyfile(BACKTESTINGPAIRSDATABASE, OLDBACKTESTINGPAIRSDATABASE)
		return True

	def copyPairsTable(self):
		"""
		V případě offline modu zkopíruje staršídatabáze ze
		složky do backtestingového umístění.
		:return:
		"""
		# Kontrola zda máme starší databázi:
		# TODO: Zde bych měl vypsat chybové hlášení pokud stará databáze neexistuje a ukončit program.
		if os.path.exists(OLDBACKTESTINGPAIRSDATABASE) is True and os.path.exists(BACKTESTINGPAIRSDATABASE) is False:
			shutil.copyfile(OLDBACKTESTINGPAIRSDATABASE, BACKTESTINGPAIRSDATABASE)
		return True

	def AllPairsFromDatabase(self):
		"""
		Vyzíská páry z databáze,
		kam jsme je umístili abychom co nejméně
		zatěžovali servery z btc-e, v případě, že testujeme
		všechny páry, v opačném případě je vyzíská z nastavení.
		:return set:
		"""
		pairs = []

		con = sqlite3.connect(BACKTESTINGPAIRSDATABASE)
		cur = con.cursor()
		for pair in cur.execute("SELECT * FROM pairs"):
			pairs.append(pair[0])
		con.close()
		# Unique
		return set(pairs)

	def PairsSynchronization(self):
		"""
		Navrátí seznam párů které máme v candlesticích.
		Zde nám dochází k synchronizaci aktuálních párů
		na směnárně a párů z databáze candlesticků.
		Návratocou hodnotou je tedy množina aktuálních
		párů z databáze candlesticků.
		:return:
		"""

		def getcurrencies2skip():
			"""
			Načte
			:return:
			"""
			file = CURRENCIES2SKIPFILE
			allpairs = []
			fout = open(file, "r", encoding="UTF-8")
			for i in fout:
				i = str(i)
				allpairs.append(i.rstrip('\n'))
			return allpairs

		currencies2skip = getcurrencies2skip()
		candlespairs = []
		allpairs = self.AllPairsFromDatabase()
		scon = sqlite3.connect(BACKTESTINGCANDLESDATABASE)
		scur = scon.cursor()
		for pair in allpairs:
			try:
				# Zde odfiltrujeme nechtěné páry:
				split = pair.split("_")
				if split[0] not in currencies2skip and split[1] not in currencies2skip:
					# Pokud je pár přítomen i v databázi candlesticků,
					# bude přidán do seznamu obchodovaných párů.
					scur.execute("SELECT * FROM candlesticks_" + pair)
					candlespairs.append(pair)
			except Exception as e:
				pass
		return set(candlespairs)

	def SavePairs2TextFile(self):
		"""
		Tato funkce uloží synchronizované páry do
		textového souboru. Tam je můžeme upravovat.
		:return:
		"""
		pairs2write = self.PairsSynchronization()
		file = PAIRS2TESTFILE
		fout = open(file, "w", encoding="UTF-8")
		for i in pairs2write:
			i = str(i) + "\n"
			fout.write(i)
		fout.close()
		return True

	def Pairs4Testing(self):
		"""
		Načte páry k testování z textového souboru.
		:return:
		"""
		file = PAIRS2TESTFILE
		allpairs = []
		fout = open(file, "r", encoding="UTF-8")
		for i in fout:
			i = str(i)
			allpairs.append(i.rstrip('\n'))
		return allpairs

	def buildIndicatorsTable(self):
		"""
		Tato funkce postaví databázi pro nová data
		oscilátorů.
		:return:
		"""
		con = sqlite3.connect(BACKTESTINGINDICATORSDATABASE)
		cur = con.cursor()

		for pair in self.alltestingpairs:
			cur.execute(
				"CREATE TABLE IF NOT EXISTS {p}("
				"avg_price,"
				"NATR,"
				"RSI,"
				"STOCH_K,"
				"STOCH_D,"
				"MACD,"
				"MACDsign,"
				"MACDhist,"
				"TRIMAultrafast,"
				"TRIMAfast,"
				"TRIMAslow,"
				"AD,"
				"BOP,"
				"MOM"
				")".format(p="signals_" + pair, ))
		con.commit()
		con.close()

	def buildSignalsTable(self):
		"""
		Tato funkce postaví databázi pro nová data
		oscilátorů.
		:return:
		"""
		con = sqlite3.connect(BACKTESTINGSIGNALSDATABASE)
		cur = con.cursor()
		for pair in self.alltestingpairs:
			cur.execute(
				"CREATE TABLE IF NOT EXISTS {p}("
				"RSIema,"
				"MACDema,"
				"STOCHema,"
				"TRIMAultraslow,"
				"ADema,"
				"BOPema,"
				"NATRema,"
				"MOMema"
				")".format(p="signals_" + pair, ))
		con.commit()
		con.close()

	def refillIndicatorsDatabases(self):
		"""
		Tato funkce znovupostaví indikátory.
		Tudíž můžeme měnit jejich nastavení.
		:return:
		"""
		con = sqlite3.connect(BACKTESTINGINDICATORSDATABASE)
		cur = con.cursor()

		def fetchData():
			scon = sqlite3.connect(BACKTESTINGCANDLESDATABASE)
			scur = scon.cursor()
			bigdata = []
			for pair in self.alltestingpairs:
				newdict = {
					"pair": pair,
					"length": [],
					"opens": [],
					"closes": [],
					"minima": [],
					"maxima": [],
					"averages": [],
					"volumes": [],
					"volumes_currency": []
				}
				for i in scur.execute("SELECT * FROM candlesticks_" + pair):
					newdict["length"].append(i[0])
					newdict["opens"].append(i[3])
					newdict["closes"].append(i[4])
					newdict["minima"].append(i[5])
					newdict["maxima"].append(i[6])
					newdict["averages"].append(i[7])
					newdict["volumes"].append(i[8])
					newdict["volumes_currency"].append(i[9])

				bigdata.append(newdict)
			scon.close()
			return bigdata

		bigdata = fetchData()
		for dat in bigdata:
			if int(len(dat["length"])) < int(2 * self.candleslength):
				print("Data pro backtesting nejsou dostatečně dlouhá.\n "
				      "Pro backtesting potřebuji alespon dvounásobek délky dat,\n"
				      "jakou používám pro aktivaci obchodů. ")
				break
			else:
				forward = 0
				cutend = forward + self.candleslength
				while cutend <= len(dat["length"]):
					nextdict = {
						"pair": dat["pair"],
						"opens": dat["opens"][forward:cutend],
						"closes": dat["closes"][forward:cutend],
						"lows": dat["minima"][forward:cutend],
						"highs": dat["maxima"][forward:cutend],
						"averages": dat["averages"][forward:cutend],
						"volumes": dat["volumes"][forward:cutend],
						"volumes_currency": dat["volumes_currency"][forward:cutend]
					}

					trima = self.indicators.trima(nextdict["averages"])
					macd = self.indicators.macd(nextdict["averages"])
					stochastic = self.indicators.stochastic(nextdict["highs"], nextdict["lows"], nextdict["closes"])
					newdict = {
						"pair": nextdict["pair"],
						"price": nextdict["averages"][-1],
						"natr": self.indicators.natr(nextdict["highs"], nextdict["lows"], nextdict["closes"]),
						"rsi": self.indicators.rsi(nextdict["averages"]),
						"stoch_k": stochastic[0],
						"stoch_d": stochastic[1],
						"macd": float(macd[0]),
						"macdsignal": float(macd[1]),
						"macdhistogram": float(macd[2]),
						"trimaultrafast": float(trima[0]),
						"trimafast": float(trima[1]),
						"trimaslow": float(trima[2]),
						"ad": self.indicators.ad(nextdict["highs"], nextdict["lows"], nextdict["closes"],
						                         nextdict["volumes_currency"]),
						"bop": self.indicators.bop(nextdict["opens"], nextdict["highs"], nextdict["lows"],
						                           nextdict["closes"]),
						"mom": self.indicators.mom(nextdict["averages"])
					}

					stringquery = 'INSERT INTO signals_' + newdict["pair"] + '(avg_price, NATR, RSI, STOCH_K, '\
					                                                         'STOCH_D,'\
					                                                         ' MACD, MACDsign, MACDhist,'\
					                                                         ' TRIMAultrafast, TRIMAfast, TRIMAslow,'\
					                                                         ' AD, BOP, MOM'\
					                                                         ')' + ' VALUES(?,?,?,?,?,?,?,?,?,?,?,'\
					                                                               '?,'\
					                                                               '?,?)'
					val = [newdict["price"], newdict["natr"], newdict["rsi"], newdict["stoch_k"], newdict["stoch_d"],
					       newdict["macd"], newdict["macdsignal"], newdict["macdhistogram"],
					       newdict["trimaultrafast"], newdict["trimafast"], newdict["trimaslow"],
					       newdict["ad"], newdict["bop"], newdict["mom"]
					       ]
					cur.execute(stringquery, val)
					forward += 1
					cutend = forward + self.candleslength
					continue
				con.commit()
		con.close()
		return True

	def refillSignalsDatabases(self):
		"""
		Tato funkce znovupostaví indikátory.
		Tudíž můžeme měnit jejich nastavení.
		:return:
		"""
		con = sqlite3.connect(BACKTESTINGSIGNALSDATABASE)
		cur = con.cursor()

		def fetchData():
			scon = sqlite3.connect(BACKTESTINGINDICATORSDATABASE)
			scur = scon.cursor()
			bigdata = []
			for pair in self.alltestingpairs:
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

		bigdata = fetchData()
		for dat in bigdata:
			if len(dat["rsi"]) < (2 * self.tradedatalength):
				print("Data pro backtesting nejsou dostatečně dlouhá.\n "
				      "Pro backtesting potřebuji alespon dvounásobek délky dat,\n"
				      "jakou používám pro aktivaci obchodů. ")
				break
			else:
				forward = 0
				cutend = forward + self.tradedatalength
				while cutend <= len(dat["rsi"]):
					nextdict = {
						"pair": dat["pair"],
						"rsi": dat["rsi"][forward:cutend],
						"macd": dat["macd"][forward:cutend],
						"stoch_k": dat["stoch_k"][forward:cutend],
						"trimaultrafast": dat["trimaultrafast"][forward:cutend],
						"ad": dat["ad"][forward:cutend],
						"bop": dat["bop"][forward:cutend],
						"natr": dat["natr"][forward:cutend],
						"mom": dat["mom"][forward:cutend]
					}
					rsi = self.indicators.indicatorsTrima(nextdict["rsi"], self.config.rsiEmaSlow)
					macd = self.indicators.indicatorsTrima(nextdict["macd"], self.config.macdEmaSlow)
					stoch = self.indicators.indicatorsTrima(nextdict["stoch_k"], self.config.stochasticEmaSlow)
					trimaultraslow = self.indicators.indicatorsTrima(nextdict["trimaultrafast"],
					                                                 self.tradedatalength)
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
						"pair"] + '(RSIema, MACDema, STOCHema, TRIMAultraslow, ADema, BOPema, NATRema, Momema)' +\
					              ' VALUES(?,'\
					              '?,?,?,'\
					              '?,'\
					              '?,?,?)'
					val = [newdict["rsiema"], newdict["macdema"], newdict["stochasticema"],
					       newdict["trimaultraslow"],
					       newdict["adema"], newdict["bopema"], newdict["natrema"], newdict["momema"]]
					cur.execute(stringquery, val)
					forward += 1
					cutend = forward + self.tradedatalength
					continue
				con.commit()
		con.close()
		return True

	def buildAndFillAll(self):
		"""
		Postaví a naplní kompletní databáze.
		:return:
		"""
		# Vyčistím terminál a podám zprávu o výstavbě databází.
		self.printer.start0_databases()
		if self.online:
			self.buildPairsTable()
		else:
			self.copyPairsTable()
		if self.online:
			if self.loadnewtradingpairs:
				self.SavePairs2TextFile()
				self.backconfig.wait4PairsAdjust()
		if self.singlePairBacktest:
			self.alltestingpairs = list()
			self.alltestingpairs.append(str(self.testingpair))
			self.alltestingpairs = tuple(self.alltestingpairs)
		else:
			self.alltestingpairs = self.Pairs4Testing()
		self.buildIndicatorsTable()
		self.buildSignalsTable()
		self.refillIndicatorsDatabases()
		self.refillSignalsDatabases()
		self.printer.ready0_databases()
		return self.alltestingpairs


class FetchDataForDecisions:
	"""
	Tato třída načte data candlesticků a
	naformátuje jejich posloupnost.
	"""

	def __init__(self, alltestingpairs):
		self.config = Helper.Config()
		self.alltestingpairs = alltestingpairs
		self.startpoint = None
		self.endpoint = None

	def fetchData(self):
		"""
		Vyzíská data z databáze indikátorů, přiřadí je do slovníků a
		vystřihne správnou délku. Projede databáze všech indikátorů a
		navrátí je ve velkém seznamu.
		:return:
		"""
		con = sqlite3.connect(BACKTESTINGCANDLESDATABASE)
		cur = con.cursor()
		icon = sqlite3.connect(BACKTESTINGINDICATORSDATABASE)
		icur = icon.cursor()
		scon = sqlite3.connect(BACKTESTINGSIGNALSDATABASE)
		scur = scon.cursor()
		bigdata = []
		pairs = tuple(self.alltestingpairs)
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
				cutlength = int(len(newdict["trimaultraslow"]))
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

	def cutData(self, fulldataset, startpoint):
		"""
		Vyřízne z velkého datasetu potřebnou posloupnost
		dat, což simuluje průběh v reálném čase.
		Fulldataset je předán jako argument.
		:param fulldataset:
		:param startpoint:
		:return:
		"""
		self.startpoint = int(startpoint)
		self.endpoint = int(int(self.startpoint) + int(self.config.overalldatalenght))
		data = []
		for newdict in fulldataset:
			nextdict = {}
			# Zde vyřízneme potřebnou délku. Poslední člen každého seznamu hodnot,
			# je posledním, tudíž nejaktuálnějším členem v databázi.
			if len(newdict["avg_price"]) >= self.endpoint:
				nextdict["pair"] = newdict["pair"]
				nextdict["avg_price"] = newdict["avg_price"][self.startpoint:self.endpoint]
				nextdict["volumes"] = newdict["volumes"][self.startpoint:self.endpoint]
				nextdict["natr"] = newdict["natr"][self.startpoint:self.endpoint]
				nextdict["rsi"] = newdict["rsi"][self.startpoint:self.endpoint]
				nextdict["stoch_k"] = newdict["stoch_k"][self.startpoint:self.endpoint]
				nextdict["stoch_d"] = newdict["stoch_d"][self.startpoint:self.endpoint]
				nextdict["macd"] = newdict["macd"][self.startpoint:self.endpoint]
				nextdict["macdsignal"] = newdict["macdsignal"][self.startpoint:self.endpoint]
				nextdict["macdhistogram"] = newdict["macdhistogram"][self.startpoint:self.endpoint]
				nextdict["trimaultrafast"] = newdict["trimaultrafast"][self.startpoint:self.endpoint]
				nextdict["trimafast"] = newdict["trimafast"][self.startpoint:self.endpoint]
				nextdict["trimaslow"] = newdict["trimaslow"][self.startpoint:self.endpoint]
				nextdict["ad"] = newdict["ad"][self.startpoint:self.endpoint]
				nextdict["bop"] = newdict["bop"][self.startpoint:self.endpoint]
				nextdict["mom"] = newdict["mom"][self.startpoint:self.endpoint]
				nextdict["rsiema"] = newdict["rsiema"][self.startpoint:self.endpoint]
				nextdict["macdema"] = newdict["macdema"][self.startpoint:self.endpoint]
				nextdict["stochema"] = newdict["stochema"][self.startpoint:self.endpoint]
				nextdict["trimaultraslow"] = newdict["trimaultraslow"][self.startpoint:self.endpoint]
				nextdict["adema"] = newdict["adema"][self.startpoint:self.endpoint]
				nextdict["bopema"] = newdict["bopema"][self.startpoint:self.endpoint]
				nextdict["natrema"] = newdict["natrema"][self.startpoint:self.endpoint]
				nextdict["momema"] = newdict["momema"][self.startpoint:self.endpoint]
				data.append(nextdict)
		return data


class Backtesting:
	"""
	Tato třída je třídou pro backtesting.
	Řídí stavbu databází, obdrží data a
	vyhodnocuje je.
	"""

	def __init__(self, data, pairs):
		self.config = Helper.Config()
		self.buyslipage = self.config.buySlipage
		self.sellslipage = self.config.sellSlipage
		self.fetch = FetchDataForDecisions(pairs)
		# Počáteční stav je jen v USD, tak jej můžu přiřadit přímo z nastavení.
		self.initializedDolars = self.config.initialDolars
		self.data = data
		self.alltestingpairs = pairs
		self.logger = Logger.BacktesterLogging()
		self.printer = Printer.BacktesterPrinter()
		self.results = ProceedAlgorythms.AllDecisionsAndStrategies()
		self.finishedDolars = None
		self.buyscounter = 0
		self.sellscounter = 0
		self.tradescounter = 0
		self.cyklecounter = 1
		self.currentprices = {}
		self.boughts = []
		self.trades4graphs = []
		self.suggestions4graphs = []
		# Přiřazení proměnných z místních metod:
		# Počáteční stav účtu využíváme pro konečný výpočet výdělku.
		self.initialAccountState = self.getInitializedAccountState()
		# Na počátku je současný stav, také inicializačním stavem účtu.
		self.currentfunds = self.getInitializedAccountState()
		self.ilength = self.iterationlength()

	def getAllPairsInfo(self):
		"""
		Načte informace o párech jež obchodujeme.
		"""
		pairsinfolist = []
		con = sqlite3.connect(PAIRSDATABASE)
		cur = con.cursor()
		for pair in cur.execute("SELECT * FROM pairs"):
			if str(pair[0]) in self.alltestingpairs:
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
		:param pair:
		"""
		for i in self.getAllPairsInfo():
			if i["pair"] == pair:
				return i

	def testingCurrencies(self):
		"""
		Vyextrahuje jednotlivé měny z databáze.
		Tyto měny nejsou všemi měnami, které můžeme mít
		na btc_e, ale pouze všechny měny se kterými se
		aktuálně obchoduje.
		:return:
		"""
		tmp = []
		for pair in self.alltestingpairs:
			split = pair.split("_")
			for i in split:
				tmp.append(i)
		tmp = set(tmp)
		return tmp

	def getInitializedAccountState(self):
		"""
		Získá inicializační stav účtu.
		:return:
		"""
		allcurrencies = {}
		currencies = self.testingCurrencies()
		for i in currencies:
			allcurrencies[i] = float(0.0)
		usdstate = {}
		usdstate["usd"] = self.config.initialDolars
		allcurrencies.update(usdstate)
		return allcurrencies

	def getFinishedDolarsState(self):
		"""
		Propočítává současný stav účtu v USD.
		To je dobré na výpočet úspěšnosti
		obchodování atd.
		:return:
		"""
		usd = float(0.0)
		for key, value in self.currentfunds.items():
			if key != "usd" and value > 0.0:
				priceskey = (str(key), "usd")
				priceskey = "_".join(priceskey)
				if priceskey in self.alltestingpairs:
					for k, v in self.currentprices.items():
						if k == str(priceskey):
							amount = value * v
							usd += amount
				else:
					priceskey = ("usd", str(key))
					priceskey = "_".join(priceskey)
					if priceskey in self.alltestingpairs:
						for k, v in self.currentprices.items():
							if k == str(priceskey):
								amount = value * v
								usd += amount
					else:
						print("Nedokázal jsem převést ", str(key), " na USD!")
			elif key == "usd" and value > 0.0:
				usd += value
			else:
				pass
		self.finishedDolars = float(usd)

	def updatemyfunds(self, currency, amount):
		"""
		Aktualizuje stav mého účtu.
		Argument pro amount může být
		i záporné hodnoty, pokud došlo k
		odprodeji měny.
		Pokud je amount == 0.0, bude hodnota
		měny na účtě vynulována.
		:param amount:
		:param currency:
		:return:
		"""
		fund = {}
		for key, value in self.currentfunds.items():
			if key == currency:
				# Pokud jsem zadal argument 0.0 bude hodnota vynulována.
				if amount != 0.0:
					newvalue = value + amount
				else:
					newvalue = 0.0
				fund[key] = newvalue
				self.currentfunds.update(fund)
			else:
				pass

	def iterationlength(self):
		"""
		Tato funkce na základě plného rozsahu dat
		z databáze vypočítá délku iterace.
		:return:
		"""
		for i in self.data:
			return int(len(i["avg_price"]))

	def Trade(self):
		"""
		Vlastní metoda obchodování, zastřešující
		celý proces simulace obchodování.
		:return:
		"""

		def oneCykle():
			"""
			Jeden cyklus pro nákupy i prodeje.
			:return:
			"""
			cut = self.fetch.cutData(self.data, int(self.cyklecounter))

			# Funkce, které budu potřebovat.
			def updateprices():
				"""
				Aktualizuje ceny párů ve slovníku self.currentprices.
				:return:
				"""
				self.currentprices = {}
				for i in cut:
					pair = None
					currprice = None
					for key, value in i.items():
						if key == "avg_price":
							currprice = value[-1]
						elif key == "pair":
							pair = value
						else:
							pass
						self.currentprices[pair] = currprice

			def getlists():
				"""
				Navrací seznamy pro prodej a nákup a
				sestaví a zapíše doporučení k prodeji
				a nákupu.
				:return:
				"""
				selllist = []
				buylist = []
				results = self.results.applyAll(cut, self.alltestingpairs, self.boughts)
				buylist = results[0]
				selllist = results[1]
				# Logování:
				if selllist:
					self.logger.logsellrecommandations(selllist)
					# Zapis do suggestions:
					for i in selllist:
						tradedict = {}
						pairtosell = None
						for key, value in i.items():
							if key == "pair":
								pairtosell = value
						tradedict = {
							"pair": pairtosell,
							"trade": "sugg2sell",
							"cykle": self.cyklecounter,
							"price": self.currentprices[pairtosell]
						}
						self.suggestions4graphs.append(tradedict)
				if buylist:
					self.logger.logbuyrecommandations(buylist)
					# Zapis do suggestions:
					for i in buylist:
						tradedict = {}
						pair2buy = None
						for key, value in i.items():
							if key == "pair":
								pair2buy = value
						tradedict = {
							"pair": pair2buy,
							"trade": "sugg2buy",
							"cykle": self.cyklecounter,
							"price": self.currentprices[pair2buy]
						}
						self.suggestions4graphs.append(tradedict)

				return selllist, buylist

			# Akce v rámci celého jednoho cyklu:
			# Získání seznamů pro prodej a nákuself.testingpairp:
			updateprices()
			seznamy = getlists()
			sells = seznamy[0]
			buys = seznamy[1]

			def processsells():
				"""
				Zprocesuje prodeje.
				Prodeje jako první z toho důvodu,
				abychom získali měnu na případné
				okamžité nákupy.
				:return:
				"""

				# Funkce které budeme potřebovat pro simulaci prodejů.
				def getBoughtPairs():
					"""
					Vyzíská ze self.boughts páry,
					které jsme nakoupili.
					:return:
					"""
					pairs = []
					if self.boughts:
						for i in self.boughts:
							for key, value in i.items():
								if key == "pair":
									pairs.append(value)
					return pairs

				def getBuyAlgorythm(pair):
					algo = None
					if self.boughts:
						for i in self.boughts:
							for key, value in i.items():
								if key == "pair" and value == pair:
									algo = i["algorythm"]
					return algo

				# Vlastní zpracování.
				# Pokud máme páry k prodeji:
				if sells:
					# Pro každý pár k prodeji:
					for i in sells:
						# Získej posloupnost nakoupených párů:
						boughtpairs = getBoughtPairs()
						# Pár k prodeji...
						pairtosell = None
						# a jeho algorytmus.
						buyingalgorythm = None
						# Přiřazujeme z proměnné 'i'...
						for key, value in i.items():
							if key == "pair":
								pairtosell = value
							elif key == "algorythm":
								buyingalgorythm = value
						# Pokud je pár k prodeji mezi nakoupenými páry:
						if pairtosell in boughtpairs:
							split = pairtosell.split("_")
							# První je měna kterou prodáváme...
							sellcurrency = split[0]
							# a druhá měna za kterou prodáváme.
							buycurrency = split[1]
							# Budeme potřebovat potvrdit ten samý algorytmus pro nákup i prodej,
							# vzhledem k tomu, že využíváme více algorytmů.
							sellingalgorythm = getBuyAlgorythm(pairtosell)
							# Pokud se nákupní a prodejní algorytmy rovnají, anebo
							# pokud je nákupní algorytmus == 0, což značí pokyn
							# pro emergency sell.
							if buyingalgorythm == sellingalgorythm or buyingalgorythm == 0:
								# Pro klíč a hodnotu v současném stavu účtu:
								for k, v in self.currentfunds.items():
									# Pokud klíč == sellkurency a hodnota > 0.0 .
									if k == sellcurrency and v > 0.0:
										amount = v * self.currentprices[pairtosell]
										# započteme poplatky a slipage:
										amount -= (amount / 100) * (float(self.config.sellSlipage) + float(
											0.2))
										self.updatemyfunds(buycurrency, +amount)
										self.updatemyfunds(sellcurrency, 0.0)
										for n in self.boughts:
											if n["pair"] == pairtosell:
												self.boughts.remove(n)
										self.sellscounter += 1
										self.tradescounter += 1
										sells.remove(i)
										self.printer.printsell(pairtosell, self.tradescounter,
										                       self.currentprices[pairtosell])
										# Zápis do grafu:
										tradedict = {
											"pair": pairtosell,
											"trade": "sell",
											"cykle": self.cyklecounter,
											"price": self.currentprices[pairtosell]
										}
										self.trades4graphs.append(tradedict)
										# Log sell:
										self.logger.logsell(pairtosell, self.cyklecounter, self.tradescounter,
										                    self.currentprices[pairtosell], self.currentfunds)
									else:
										pass
							else:
								pass
						else:
							pass
				else:
					pass

			def processbuys():
				"""
				Zprocesuje nákupy.
				:return:
				"""

				def getBoughtPairs():
					"""
					Vyzíská ze self.boughts páry,
					které jsme nakoupili.
					:return:
					"""
					pairs = []
					if self.boughts:
						for i in self.boughts:
							for key, value in i.items():
								if key == "pair":
									pairs.append(value)
					return pairs

				# Pokud máme pokyny k nákupům:
				if buys:
					# Pro každý pár:
					for i in buys:
						# {'price': 656.889608433736, 'sequencialbuy': 5, 'algorythm': 1, 'pair': 'btc_usd'}
						pair = None
						sequencialbuy = None
						for key, value in i.items():
							if key == "pair":
								pair = str(value)
							elif key == "sequencialbuy":
								sequencialbuy = int(value)
						split = pair.split("_")
						# Nakupujeme první měnu v měnovém páru:
						buycurrency = split[0]
						# Prodáváme druhou měnu v měnovém páru:
						sellcurrency = split[1]
						# Zápis do self.currentfunds:
						for k, v in self.currentfunds.items():
							if k == sellcurrency and v > 0.0:
								buyamount = (float(v) / float(self.currentprices[pair]))
								# Odečítáme slipage a poplatky.
								buyamount -= (buyamount / 100) * (
									float(self.config.sellSlipage) + float(0.2))
								sellamount = -v
								buyamount /= sequencialbuy
								sellamount /= sequencialbuy
								self.updatemyfunds(buycurrency, buyamount)
								self.updatemyfunds(sellcurrency, sellamount)
								self.boughts.append(i)
								self.buyscounter += 1
								self.tradescounter += 1
								buys.remove(i)
								self.printer.printbuy(pair, self.tradescounter, self.currentprices[pair])
								tradedict = {
									"pair": pair,
									"trade": "buy",
									"cykle": self.cyklecounter,
									"price": self.currentprices[pair]
								}
								self.trades4graphs.append(tradedict)
								self.logger.logbuy(pair, self.cyklecounter, self.tradescounter,
								                   self.currentprices[pair], self.currentfunds)
							else:
								pass
				else:
					pass

			processsells()
			processbuys()

		def runFullCykles():
			"""
			Funkce která rozeběhne a kontroluje celou metodu.
			:return:
			"""

			def cleanOlds():
				"""
				Vyčistí staré záznamy a logy.
				:return:
				"""
				os.chdir("./Backtesting/backtesting_logs")
				filelist = [f for f in os.listdir(".") if f.endswith(".log")]
				for f in filelist:
					os.remove(f)
				os.chdir("../..")

			cleanOlds()
			iterlength = self.ilength
			# Počáteční akce:
			if self.cyklecounter == 1:
				# Tisk do terminálu:
				self.printer.printtradesbegin(self.currentfunds, self.initializedDolars)
				# Zalogování:
				self.logger.logtradesbegin(self.currentfunds, self.initializedDolars)
			# Spuštění samotnáho backtestingu:
			while self.cyklecounter < iterlength - self.config.overalldatalenght:
				oneCykle()
				self.cyklecounter += 1
			# Konečný výsledek:
			self.getFinishedDolarsState()
			# Výpočet výsledku v procentech.
			procent = float(
				(float(self.finishedDolars) - float(self.initializedDolars)) / (float(self.initializedDolars) / 100))
			# Tisk do terminálu:
			self.printer.printtradesend(self.currentfunds, self.finishedDolars, self.buyscounter, self.sellscounter,
			                            self.tradescounter, self.cyklecounter, procent)
			# Zalogování:
			self.logger.logtradesresults(self.currentfunds, self.finishedDolars, self.buyscounter, self.sellscounter,
			                             self.tradescounter, procent)
			return self.trades4graphs, self.suggestions4graphs

		return runFullCykles()


"""
Navrat self.trades4graphs, příklad:
[
{'price': 564.893373493975, 'trade': 'buy', 'pair': 'btc_usd', 'cykle': 2},
{'price': 0.000655, 'trade': 'buy', 'pair': 'nmc_btc', 'cykle': 101},
{'price': 0.000674759036, 'trade': 'sell', 'pair': 'nmc_btc', 'cykle': 114},
{'price': 0.000665, 'trade': 'buy', 'pair': 'ppc_btc', 'cykle': 116},
{'price': 0.000561111111, 'trade': 'sell', 'pair': 'ppc_btc', 'cykle': 424},
{'price': 0.024754743976, 'trade': 'buy', 'pair': 'eth_btc', 'cykle': 438},
{'price': 0.023489533133, 'trade': 'sell', 'pair': 'eth_btc', 'cykle': 615},
{'price': 0.000651786787, 'trade': 'buy', 'pair': 'nmc_btc', 'cykle': 676},
{'price': 0.000555208955, 'trade': 'sell', 'pair': 'nmc_btc', 'cykle': 2578},
{'price': 648.04002245509, 'trade': 'sell', 'pair': 'btc_usd', 'cykle': 2579},
{'price': 0.3685, 'trade': 'buy', 'pair': 'nmc_usd', 'cykle': 2660},
{'price': 0.30752238806, 'trade': 'sell', 'pair': 'nmc_usd', 'cykle': 2854},
{'price': 0.704188622754, 'trade': 'buy', 'pair': 'nvc_usd', 'cykle': 2919},
{'price': 0.668, 'trade': 'sell', 'pair': 'nvc_usd', 'cykle': 3247},
{'price': 0.326785714286, 'trade': 'buy', 'pair': 'nmc_usd', 'cykle': 3251},
{'price': 0.314241791045, 'trade': 'sell', 'pair': 'nmc_usd', 'cykle': 3395}
]
"""


class PlotGraphs:
	"""
	Tato tříta vykreslí grafy. V závislosti na
	nastavení můžeme vykreslovat grafy bez obchodů,
	či s nasimulovanými obchody. Pro vykreslení grafů,
	bez nasimulovaných obchodů využijeme páry z nastavení.
	Pro vykreslení grafů s nasimulovanými obchody, využijeme
	seznamy zobchodovaných párů.
	"""

	def __init__(self, data, pairs):
		self.backconfig = Config4Backtesting()
		self.singlepairbacktesting = bool(self.backconfig.singlePairBacktest)
		self.tradessimulation = bool(self.backconfig.tradessimulation)
		self.config = Helper.Config()
		self.data = data
		self.pairs = pairs

	def getPairs2plot(self, trades=None):
		"""
		V závislosti na nastavení vrátí páry k
		zobrazení.
		:return:
		"""
		pairs2plot = []
		if trades is None:
			trades = []
		# Pokud simulujeme obchody, chceme páry jež byly zobchodovány.
		if self.tradessimulation:
			if trades:
				# Pokud proběhly obchody, extrahujeme zobchodované páry.
				pairs2plot = [x["pair"] for x in trades]
				pairs2plot = set(pairs2plot)
			else:
				# Pokud mi neproběhl žádný obchod jen vykreslím grafy.
				# Pokud backtestujeme jen jeden pár:
				if self.singlepairbacktesting:
					pairs2plot.append(str(self.backconfig.plotpair))
				# Jinak načteme páry ze souboru.
				else:
					pairs2plot = self.pairs
		# Jinak načítáme páry z nastavení.
		else:
			# Pokud backtestujeme jen jeden pár:
			if self.singlepairbacktesting:
				pairs2plot.append(str(self.backconfig.plotpair))
			# Jinak načteme páry ze souboru.
			else:
				pairs2plot = self.pairs
		return set(pairs2plot)

	def filterSuggestions(self, pairs2plot=None, suggestions=None):
		"""
		Profiltruje návrhy k nákupům s zobchodovanými páry.
		:return:
		"""
		if pairs2plot is None:
			pairs2plot = set()
		if suggestions is None:
			suggestions = set()
		suggestions2return = list()
		suggestionspairs = set()
		# Pokud máme páry k vykreslení a doporučení:
		if pairs2plot and suggestions:
			pairs2plot = set(pairs2plot)
			# Pokud proběhly obchody, extrahujeme zobchodované páry
			# a převedeme na množinu jedinečných prvků.
			suggestionspairs = set([x["pair"] for x in suggestions])
			# Ty nyní synchronizujeme s páry jež byly reálně zobchodovány.
			suggestionspairs = set([d for d in suggestionspairs if d in pairs2plot])
			# suggestions2return naplníme hodnotami:
			for p in suggestionspairs:
				for i in suggestions:
					if i["pair"] == p:
						suggestions2return.append(i)
		return suggestions2return

	def plotSingleGraph(self, pair, trades=None, suggestions=None):
		"""
		Vymodeluje grafy candlesticků.
		:return:
		"""
		pair = str(pair)
		print("Vykresluji graf pro " + pair + ".\n")
		# Pro vykreslení bez obchodů.
		if trades is None:
			trades = []
		# Extrakce obchodů pro náš pár:
		else:
			trades = [x for x in trades if x["pair"] == pair]
		# Pro vykreslení bez obchodů.
		if suggestions is None:
			suggestions = []
		# Extrakce doporučení pro náš pár:
		else:
			suggestions = [x for x in suggestions if x["pair"] == pair]
		quotes = None
		volume = None
		date = None

		def getdataset4candles():
			volume = None
			date = None
			quotes = []
			tick = None
			for i in self.data:
				if i["pair"] == pair:
					c = 0
					volume = i["volumes"]
					date = i["length"]
					while c < len(date):
						tick = int(c + 1), i["opens"][c], i["closes"][c], i["maxima"][c], i["minima"][c],\
						       i["volumes"][c]
						c += 1
						quotes.append(tuple(tick))
			return quotes, volume, date

		def getindicatorsdata(indicator):
			"""
			Navrací posloupnost dat indikátorů.
			:param indicator:
			:return:
			"""
			indicator = str(indicator)
			for i in self.data:
				if i["pair"] == pair:
					return i[indicator]

		# Kompletni okno:
		fig = plt.figure(facecolor='black')
		# DATA:
		candlesticksdata, volume, date = getdataset4candles()

		# RSI graf:
		rsi = getindicatorsdata("rsi")
		rsiema = getindicatorsdata("rsiema")
		ax0 = plt.subplot2grid((11, 4), (0, 0), rowspan=1, colspan=4, axisbg='black')
		ax0.plot(date, rsi, color='#00ffe8', linewidth=0.8, label="RSI")
		ax0.plot(date, rsiema, color='#FFDF00', linewidth=0.9, label="RSIema")
		ax0.legend(prop={'size': 6})
		ax0.set_ylim(0, 100)
		ax0.axhline(self.config.rsiBotom, color='w', alpha=0.5)
		ax0.axhline(self.config.rsiRoof, color='w', alpha=0.5)
		ax0.axhline(50.0, color='w', alpha=0.5)
		# Ohraniceni grafu:
		ax0.spines['bottom'].set_color("#FFD700")
		ax0.spines['top'].set_color("#FFD700")
		ax0.spines['right'].set_color("#FFD700")
		ax0.spines['left'].set_color("#FFD700")
		ax0.tick_params(axis='x', colors='w')
		ax0.tick_params(axis='y', colors='w')
		ax0.set_yticks([50.0, self.config.rsiBotom, self.config.rsiRoof])
		ax0.yaxis.label.set_color('w')
		plt.ylabel('RSI', color='w')

		# Svíčkový graf
		ax1 = plt.subplot2grid((11, 4), (1, 0), rowspan=3, colspan=4, axisbg='black', sharex=ax0)
		candlestick(ax1, candlesticksdata, width=0.5, colorup='g', colordown='r')
		ax1.grid(True, color='w')
		# EMA:
		trimaslow = getindicatorsdata("trimaslow")
		trimafast = getindicatorsdata("trimafast")
		trimaultrafast = getindicatorsdata("trimaultrafast")
		trimaultraslow = getindicatorsdata("trimaultraslow")
		ax1.plot(trimaslow, color='blue', lw=1.3, label='TRIMAslow')
		ax1.plot(trimafast, color='green', lw=1.1, label='TRIMAfast')
		ax1.plot(trimaultrafast, color='#FFDF00', lw=0.8, label='TRIMAultrafast')
		ax1.plot(trimaultraslow, color='w', lw=0.8, label='MARKETtrend')
		# Zobrazení obchodů:
		if trades:
			for i in trades:
				c = None
				if str(i["trade"]) == "buy":
					c = "#00cc00"
				elif str(i["trade"]) == "sell":
					c = "#ff0000"
				ax1.plot([int(i["cykle"] + self.config.overalldatalenght), ], [i["price"], ], 'ro', color=c)
				ax1.text(int(i["cykle"] + self.config.overalldatalenght), i["price"], str(i["trade"]), color='w')
		# Zobrazení doporučení:
		if suggestions:
			for i in suggestions:
				c = None
				if str(i["trade"]) == "sugg2buy":
					c = "#00cc00"
				elif str(i["trade"]) == "sugg2sell":
					c = "#ff0000"
				hight = [float(i["price"] + float(i["price"] / 10)), ]
				ax1.plot([int(i["cykle"] + self.config.overalldatalenght), ], hight, 'v', color=c)
		ax1.legend(prop={'size': 6})
		# label po strane:
		ax1.yaxis.label.set_color('w')
		ax1.xaxis.label.set_color('w')
		# Ohraniceni grafu:
		ax1.spines['bottom'].set_color("#FFD700")
		ax1.spines['top'].set_color("#FFD700")
		ax1.spines['right'].set_color("#FFD700")
		ax1.spines['left'].set_color("#FFD700")
		# Barva ticku (cisel) po stranach grafu:
		ax1.tick_params(axis='y', colors='w')
		plt.ylabel("PRICE", color='w')

		# VOLUMY:
		# promennou vyuzijeme pro vyplneni volumu barvou.
		volumeMin = 0
		# Druhy graf:
		ax1v = ax1.twinx()
		ax1v.fill_between(date, volumeMin, volume, facecolor='#00ffe8', alpha=0.3)
		# Potlaceni vykresleni hodnot u volumu, kde nejsou potreba.
		ax1v.axes.yaxis.set_ticklabels([])
		# Nechceme mrizku pro volumy.
		ax1v.grid(False)
		# Ohraniceni grafu:
		ax1v.spines['bottom'].set_color("#FFD700")
		ax1v.spines['top'].set_color("#FFD700")
		ax1v.spines['right'].set_color("#FFD700")
		ax1v.spines['left'].set_color("#FFD700")
		# urceni maximalni velikosti volume grafu:
		ax1v.set_ylim(0, 10 * max(volume))
		ax1v.tick_params(axis='x', colors='w')
		ax1v.tick_params(axis='y', colors='w')

		# MACD
		MACDDATA = getindicatorsdata("macd")
		MACDEMA = getindicatorsdata("macdema")
		MACDSIGNALDATA = getindicatorsdata("macdsignal")
		MACDHISTOGRAMDATA = getindicatorsdata("macdhistogram")
		ax2 = plt.subplot2grid((11, 4), (4, 0), sharex=ax0, rowspan=2, colspan=4, axisbg='black')
		ax2.axhline(0.0, color='red')
		ax2.plot(date, MACDDATA, label='MACD')
		ax2.plot(date, MACDEMA, color="#FFDF00", label='MACDema')
		ax2.plot(date, MACDSIGNALDATA, label='MACDsignal')
		ax2.plot(date, MACDHISTOGRAMDATA, label='MACDhistogram')
		ax2.legend(prop={'size': 6})
		ax2.grid(True, color='w')
		# Ohraniceni grafu:
		ax2.spines['bottom'].set_color("#FFD700")
		ax2.spines['top'].set_color("#FFD700")
		ax2.spines['right'].set_color("#FFD700")
		ax2.spines['left'].set_color("#FFD700")
		ax2.tick_params(axis='x', colors='w')
		ax2.tick_params(axis='y', colors='w')
		plt.ylabel('MACD', color='w')

		# STOCHASTIC
		STOCH_K = getindicatorsdata("stoch_k")
		STOCH_D = getindicatorsdata("stoch_d")
		STOCHEMA = getindicatorsdata("stochema")
		ax3 = plt.subplot2grid((11, 4), (6, 0), sharex=ax0, rowspan=1, colspan=4, axisbg='black')
		ax3.axhline(self.config.stochasticRoof, color='w', alpha=0.5)
		ax3.axhline(self.config.stochasticBottom, color='w', alpha=0.5)
		ax3.axhline(50.0, color='w', alpha=0.5)
		ax3.plot(date, STOCH_K, label='STOCH_k')
		ax3.plot(date, STOCH_D, label='STOCH_d')
		ax3.plot(date, STOCHEMA, label='STOCHema', linewidth=0.7)
		ax3.legend(prop={'size': 6})
		# Ohraniceni grafu:
		ax3.spines['bottom'].set_color("#FFD700")
		ax3.spines['top'].set_color("#FFD700")
		ax3.spines['right'].set_color("#FFD700")
		ax3.spines['left'].set_color("#FFD700")
		ax3.tick_params(axis='x', colors='w')
		ax3.tick_params(axis='y', colors='w')
		ax3.set_yticks([50.0, self.config.stochasticBottom, self.config.stochasticRoof])
		plt.ylabel('STOCH', color='w')

		# AD
		AD = getindicatorsdata("ad")
		ADEMA = getindicatorsdata("adema")
		ax4 = plt.subplot2grid((11, 4), (7, 0), sharex=ax0, rowspan=1, colspan=4, axisbg='black')
		ax4.axhline(0.0, color='w', alpha=0.5)
		ax4.plot(date, AD, color="#0087C1", linewidth=0.5, label='AD')
		ax4.plot(date, ADEMA, color="#FFDF00", linewidth=0.7, label='ADema')
		ax4.legend(prop={'size': 6})
		# Ohraniceni grafu:
		ax4.spines['bottom'].set_color("#FFD700")
		ax4.spines['top'].set_color("#FFD700")
		ax4.spines['right'].set_color("#FFD700")
		ax4.spines['left'].set_color("#FFD700")
		ax4.tick_params(axis='x', colors='w')
		ax4.tick_params(axis='y', colors='w')
		ax4.set_yticks([0.0])
		plt.ylabel('AD', color='w')

		# BOP
		BOP = getindicatorsdata("bop")
		BOPEMA = getindicatorsdata("bopema")
		ax5 = plt.subplot2grid((11, 4), (8, 0), sharex=ax0, rowspan=1, colspan=4, axisbg='black')
		ax5.axhline(0.0, color='w', alpha=0.5)
		ax5.plot(date, BOP, color="#0000CD", linewidth=0.5, label='BOP')
		ax5.plot(date, BOPEMA, color="red", linewidth=0.9, label='BOPema')
		ax5.legend(prop={'size': 6})
		# Ohraniceni grafu:
		ax5.spines['bottom'].set_color("#FFD700")
		ax5.spines['top'].set_color("#FFD700")
		ax5.spines['right'].set_color("#FFD700")
		ax5.spines['left'].set_color("#FFD700")
		ax5.tick_params(axis='x', colors='w')
		ax5.tick_params(axis='y', colors='w')
		ax5.set_yticks([0.0])
		plt.ylabel('BOP', color='w')

		# MOM
		MOM = getindicatorsdata("mom")
		MOMEMA = getindicatorsdata("momema")
		ax6 = plt.subplot2grid((11, 4), (9, 0), sharex=ax0, rowspan=1, colspan=4, axisbg='black')
		ax6.axhline(0.0, color='w', alpha=0.5)
		ax6.plot(date, MOM, color="#00FF00", label='MOM')
		ax6.plot(date, MOMEMA, color="#FFDF00", label='MOMema')
		ax6.legend(prop={'size': 6})
		# Ohraniceni grafu:
		ax6.spines['bottom'].set_color("#FFD700")
		ax6.spines['top'].set_color("#FFD700")
		ax6.spines['right'].set_color("#FFD700")
		ax6.spines['left'].set_color("#FFD700")
		ax6.tick_params(axis='x', colors='w')
		ax6.tick_params(axis='y', colors='w')
		ax6.set_yticks([0.0])
		plt.ylabel('MOM', color='w')

		# NATR
		NATR = getindicatorsdata("natr")
		NATREMA = getindicatorsdata("natrema")
		ax7 = plt.subplot2grid((11, 4), (10, 0), sharex=ax0, rowspan=1, colspan=4, axisbg='black')
		ax7.axhline(self.config.minvolatility, color='w', alpha=0.5)
		ax7.set_yticks([self.config.minvolatility, 0.0])
		ax7.plot(date, NATR, color="#DC143C", label='NATR')
		ax7.plot(date, NATREMA, color="#FFDF00", label='NATRema')
		ax7.legend(prop={'size': 6})
		# Ohraniceni grafu:
		ax7.spines['bottom'].set_color("#FFD700")
		ax7.spines['top'].set_color("#FFD700")
		ax7.spines['right'].set_color("#FFD700")
		ax7.spines['left'].set_color("#FFD700")
		ax7.tick_params(axis='x', colors='w')
		ax7.tick_params(axis='y', colors='w')
		plt.ylabel('NATR', color='w')

		# Nahnuti a formatovani datumu grafu:
		for label in ax7.xaxis.get_ticklabels():
			label.set_rotation(45)

		# Posunuti hranic cele figury v okne:
		plt.subplots_adjust(left=.05, bottom=.10, right=.98, top=.94, wspace=.20, hspace=0)
		# Nadpis celeho okna:
		plt.suptitle(pair.upper() + ' CHART', color='w')
		# Xlabel:
		plt.xlabel("Time Period", color='w')

		# Zabraneni vykresleni datumu pod prvnim grafem a zaroven jejich uchovani pro druhy graf.
		# plt.setp(ax1.get_xticklabels(), visible=False)
		# Potlaceni vykresleni hodnot u volumu, kde nejsou potreba.
		ax1v.axes.yaxis.set_ticklabels([])

		# Zabraneni vykresleni datumu pod prvnim grafem a zaroven jejich uchovani pro druhy graf.
		plt.setp(ax0.get_xticklabels(), visible=False)
		plt.setp(ax1.get_xticklabels(), visible=False)
		plt.setp(ax2.get_xticklabels(), visible=False)
		plt.setp(ax3.get_xticklabels(), visible=False)
		plt.setp(ax4.get_xticklabels(), visible=False)
		plt.setp(ax5.get_xticklabels(), visible=False)
		plt.setp(ax6.get_xticklabels(), visible=False)

		plt.show()
		# Uchovani obrazu:
		if self.backconfig.savegraphs:
			fig.savefig('./Backtesting/pictures/' + str(int(time.time())) + "_" + str(pair) + '_graph.png')

	def graphAll(self, trades=None, suggestions=None):
		"""
		Vykreslí všechny potřebné grafy.
		:return:
		"""
		pairs = self.getPairs2plot(trades)
		suggestions = self.filterSuggestions(pairs, suggestions)
		for i in pairs:
			self.plotSingleGraph(i, trades, suggestions)


class ControlBacktesting:
	"""
	Třída řídící backtesting.
	"""

	def __init__(self):
		self.backtesterconfig = Config4Backtesting()
		self.databases = BuildDatabases()
		self.alltestingpairs = self.databases.buildAndFillAll()
		self.fetch = FetchDataForDecisions(self.alltestingpairs)
		self.data = self.fetch.fetchData()
		self.backtesting = Backtesting(self.data, self.alltestingpairs)
		self.graphs = PlotGraphs(self.data, self.alltestingpairs)

	def run(self):
		"""
		Jádro běhu backtestingu.
		:return:
		"""
		trades = None
		suggestions = None
		if self.backtesterconfig.tradessimulation:
			trades, suggestions = self.backtesting.Trade()
			if self.backtesterconfig.plotgraphs:
				print("\nVykresluji grafy. \nMoment. \n")
				self.graphs.graphAll(trades, suggestions)
		elif self.backtesterconfig.plotgraphs:
			print("\nVykresluji grafy. \nMoment. \n")
			self.graphs.plotgraphs(trades)


####################
# Testy:
####################

if __name__ == "__main__":
	backtesting = ControlBacktesting()
	backtesting.run()
