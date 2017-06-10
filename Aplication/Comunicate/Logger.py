#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import time
import Helper


"""
Tento modul má na starosti logování programu.
"""


# ------------
# Třídy
# ------------

class ApiLogging:
	"""
	Tato třída loguje chyby ve spojení.
	"""

	def __init__(self):
		self.file = "../logs/connlogs/apiconnections.log"
		# Smazání a příprava souboru.
		fin = open(self.file, "a", encoding="UTF-8")
		fin.close()

	def logapiconnectionerror(self, meassange):
		"""
		Tato metoda zaloguje chybu spojení pro modul API.py.
		:param meassange:
		:param:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("Zachytil jsem chybu spojení modulu Api.py v čase: ")
		fin.write(str(time.asctime()))
		fin.write("\n")
		fin.write("Zpráva z modulu je:")
		fin.write("\n")
		fin.write(str(meassange))
		fin.write("\n")
		fin.close()

	def logapimethoderror(self, methodname, counter):
		"""
		Tato metoda zaloguje chybu spojení pro modul API.py.
		:param counter:
		:param methodname:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("V čase: ")
		fin.write(str(time.asctime()))
		fin.write(" metoda ")
		fin.write(str(methodname))
		fin.write(", modulu Api.py, překročila kritický počet 10 cyklů.")
		fin.write("\n")
		fin.write("Počet cyklů je: ")
		fin.write(str(counter))
		fin.write("\n")
		fin.close()


class TapiLogging:
	"""
	Tato třída loguje chyby ve spojení.
	"""

	def __init__(self):
		self.file = "../logs/connlogs/tapiconnections.log"
		# Smazání a příprava souboru.
		fin = open(self.file, "a", encoding="UTF-8")
		fin.close()

	def logtapiconnectionerror(self, meassange):
		"""
		Tato metoda zaloguje chybu spojení pro modul TAPI.py.
		:param meassange:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("Zachytil jsem chybu spojení modulu Tapi.py v čase: ")
		fin.write(str(time.asctime()))
		fin.write("\n")
		fin.write("Zpráva z modulu je:")
		fin.write("\n")
		fin.write(str(meassange))
		fin.write("\n")
		fin.close()

	def logtapimethoderror(self, methodname, counter, info):
		"""
		Tato metoda zaloguje chybu spojení pro modul API.py.
		:param info:
		:param counter:
		:param methodname:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("V čase: ")
		fin.write(str(time.asctime()))
		fin.write(" metoda ")
		fin.write(str(methodname))
		fin.write(", modulu Tapi.py, překročila kritický počet 4 cyklů.")
		fin.write("\n")
		fin.write("Počet cyklů je: ")
		fin.write(str(counter))
		fin.write("\n")
		fin.write("Zpráva ze serveru je: ")
		fin.write(str(info))
		fin.write("\n")
		fin.close()


class AplicationLogging:
	"""
	Třída, která loguje modul Backtester.py.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.file = "../logs/applogs/log"
		# Smazání a příprava souboru.
		fin = open(self.file, "a", encoding="UTF-8")
		fin.close()

	def logAplicationStart(self):
		"""
		Tato metoda zaloguje prodej.
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("V čase ")
		fin.write(str(time.asctime()))
		fin.write(" se spouští mAG_BOt.")
		fin.write("\n")

	def logAplicationEnd(self):
		"""
		Tato metoda zaloguje prodej.
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("V čase ")
		fin.write(str(time.asctime()))
		fin.write(" byl mAG_BOt vypnut.")
		fin.write("\n")

	def loggCandlesException(self):
		"""
		Tato metoda zaloguje prodej.
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("V čase ")
		fin.write(str(time.asctime()))
		fin.write(" došlo k překročení limitu prázdných candlesticků.")
		fin.write("\n")
		fin.write("Chyba je buď na straně Vašeho připojení k internetu,")
		fin.write("\n")
		fin.write("nebo na straně serveru Btce-com.")
		fin.write("\n")
		fin.close()


class TraderLogging:
	"""
	Třída, která loguje modul Backtester.py.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.file = "../logs/tradelogs/trades.log"
		# Smazání a příprava souboru.
		fin = open(self.file, "a", encoding="UTF-8")
		fin.close()

	def loggsell(self, pair, price):
		"""
		Tato metoda zaloguje prodej.
		:param price:
		:param pair:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("*" * 60)
		fin.write("\n")
		fin.write("V čase ")
		fin.write(str(time.asctime()))
		fin.write(" prodávám ")
		fin.write(str(pair))
		fin.write(" za cenu ")
		fin.write(str(price))
		fin.write(".")
		fin.write("\n")
		fin.write("*" * 60)
		fin.close()

	def loggbuy(self, pair, price):
		"""
		Tato metoda zaloguje prodej.
		:param price:
		:param pair:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("*" * 60)
		fin.write("\n")
		fin.write("V čase ")
		fin.write(str(time.asctime()))
		fin.write(" kupuji ")
		fin.write(str(pair))
		fin.write(" za cenu ")
		fin.write(str(price))
		fin.write(".")
		fin.write("\n")
		fin.write("*" * 60)
		fin.close()

	def logsellrecommandations(self, selllist):
		"""
		Tato metoda zaloguje doporučení k prodeji.
		:param selllist:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("Doporučení k prodeji jsou: ")
		fin.write(str(selllist))
		fin.write("\n")
		fin.close()

	def logbuyrecommandations(self, buylist):
		"""
		Tato metoda zaloguje doporučení k nákupu.
		:param buylist:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("Doporučení k nákupu jsou: ")
		fin.write(str(buylist))
		fin.write("\n")
		fin.close()


class BacktesterLogging:
	"""
	Třída, která loguje modul Backtester.py.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.file = "./Backtesting/backtesting_logs/backtesting.log"
		# Smazání a příprava souboru.
		fin = open(self.file, "a", encoding="UTF-8")
		fin.close()

	def logsellrecommandations(self, selllist):
		"""
		Tato metoda zaloguje doporučení k prodeji.
		:param selllist:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("Doporučení k prodeji jsou: ")
		fin.write(str(selllist))
		fin.write("\n")
		fin.close()

	def logbuyrecommandations(self, buylist):
		"""
		Tato metoda zaloguje doporučení k nákupu.
		:param buylist:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("Doporučení k nákupu jsou: ")
		fin.write(str(buylist))
		fin.write("\n")
		fin.close()

	def logsell(self, pair, cyklecounter, tradescounter, price, currentfunds):
		"""
		Tato metoda zaloguje prodej.
		:param currentfunds:
		:param price:
		:param tradescounter:
		:param cyklecounter:
		:param pair:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("-" * 40)
		fin.write("\n")
		fin.write("Candlestick č.")
		fin.write(str(cyklecounter + self.config.indicatorsLength))
		fin.write("\n")
		fin.write("Obchod č.")
		fin.write(str(tradescounter))
		fin.write("\n")
		fin.write("Prodávám ")
		fin.write(str(pair))
		fin.write(" za cenu ")
		fin.write(str(price))
		fin.write("\n")
		fin.write("Stav účtu je :")
		fin.write(str(currentfunds))
		fin.write("\n")
		fin.write("-" * 40)
		fin.write("\n")

	def logbuy(self, pair, cyklecounter, tradescounter, price, currentfunds):
		"""
		Tato metoda zaloguje prodej.
		:param currentfunds:
		:param price:
		:param tradescounter:
		:param cyklecounter:
		:param pair:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("-" * 40)
		fin.write("\n")
		fin.write("Candlestick č.")
		fin.write(str(cyklecounter + self.config.indicatorsLength))
		fin.write("\n")
		fin.write("Obchod č.")
		fin.write(str(tradescounter))
		fin.write("\n")
		fin.write("Kupuji ")
		fin.write(str(pair))
		fin.write(" za cenu ")
		fin.write(str(price))
		fin.write("\n")
		fin.write("Stav účtu je :")
		fin.write(str(currentfunds))
		fin.write("\n")
		fin.write("-" * 40)
		fin.write("\n")

	def logtradesbegin(self, currentfunds, initializeddolars):
		"""
		Tato metoda zaloguje počátek obchodování.
		:param initializeddolars:
		:param currentfunds:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("Stav financí na začátku: ")
		fin.write(str(currentfunds))
		fin.write("\n")
		fin.write("Stav financí na začátku v USD: ")
		fin.write(str(initializeddolars))
		fin.write("\n" * 3)
		fin.close()

	def logtradesresults(self, currentfunds, finishedDolars, buyscounter, sellscounter, tradescounter, procent):
		"""
		Tato metoda zaloguje výsledky obchodování.
		:param procent:
		:param tradescounter:
		:param sellscounter:
		:param buyscounter:
		:param finishedDolars:
		:param currentfunds:
		:return:
		"""
		fin = open(self.file, "a", encoding="UTF-8")
		fin.write("\n" * 3)
		fin.write("Stav financí na konci: ")
		fin.write(str(currentfunds))
		fin.write("\n")
		fin.write("Stav financí v  USD na konci: ")
		fin.write(str(finishedDolars))
		fin.write("\n")
		fin.write("Počet nákupů: ")
		fin.write(str(buyscounter))
		fin.write("\n")
		fin.write("Počet prodejů: ")
		fin.write(str(sellscounter))
		fin.write("\n")
		fin.write("Počet obchodů: ")
		fin.write(str(tradescounter))
		fin.write("\n")
		fin.write("Procentuální úspěšnost je:  ")
		fin.write(str(procent))
		fin.write("\n")
		fin.close()
