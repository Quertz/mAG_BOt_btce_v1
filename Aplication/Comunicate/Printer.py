#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import time
import Helper


"""
Tento modul má na starost výstup do terminálu.
"""


# Funkce pro formátování výstupu.
def clean():
	print("\n" * 50)


def mezera():
	print("#" * 90)


def tenkamezera():
	print("~" * 90)


# Třídy

class BacktesterPrinter:
	"""
	Tato třída obsahuje metody výstupu do
	terminálu pro modul Backtester.py.
	"""

	def __init__(self):
		pass

	def start0_databases(self):
		# Protože je to první výstup v modulu Backtester.py,
		# čistím terminál zde.
		clean()
		mezera()
		print("\n")
		print("Začínám stavět databáze.")

	def ready0_databases(self):
		print("Databáze jsou postaveny.")
		tenkamezera()

	def printtradesbegin(self, currentfunds, initializedDolars):
		"""
		Vytiskne informace na začátku testování.
		:param currentfunds:
		:param initializedDolars:
		:return:
		"""
		print("Stav financí na začátku: ", currentfunds)
		print("Stav financí na začátku v USD: ", initializedDolars)
		tenkamezera()

	def printsell(self, pair, tradescounter, price):
		"""
		Vytiskne informace o prodeji.
		:param pair:
		:param tradescounter:
		:param price:
		:return:
		"""
		print("Obchod č.", tradescounter, ". Prodávám ", pair, " za cenu ", price)

	def printbuy(self, pair, tradescounter, price):
		"""
		Vytiskne informace o prodeji.
		:param pair:
		:param tradescounter:
		:param price:
		:return:
		"""
		print("Obchod č.", tradescounter, ". Kupuji ", pair, " za cenu ", price)

	def printtradesend(self, currentfunds, finishedDolars, buyscounter,
	                   sellscounter, tradescounter, cyklecounter, procent):
		"""
		Vytiskne informace na konci obchodování.
		:param currentfunds:
		:param finishedDolars:
		:param buyscounter:
		:param sellscounter:
		:param tradescounter:
		:param cyklecounter:
		:param procent:
		:return:
		"""
		if sellscounter != 0:
			tradesprocent = procent / sellscounter
		else:
			if buyscounter == 1:
				tradesprocent = procent / buyscounter
			else:
				tradesprocent = 0
		tenkamezera()
		print("Stav financí na konci: ", currentfunds)
		print("Stav financí na konci v USD: ", finishedDolars)
		print("Počet nákupů: ", buyscounter)
		print("Počet prodejů: ", sellscounter)
		print("Počet obchodů: ", tradescounter)
		print("Počet cyklů: ", cyklecounter)
		print("Celková procentuální úspěšnost je: ", procent, "%.")
		print("Procentuální úspěšnost je ", tradesprocent, "% na obchod.")
		print("\n")
		mezera()
		print("\n" * 2)


class AplicationPrinter:
	"""
	Tato třída obsahuje metody výstupu do
	terminálu pro modul Backtester.py.
	"""

	def __init__(self):
		self.config = Helper.Config()
		now = int(time.time())
		self.delay4start = int(
			self.config.overalldatalenght + self.config.indicatorsLength) * self.config.candlestickLenght
		tradesstart = int(now + self.delay4start)
		self.starttradingtime = time.asctime(time.localtime(tradesstart))

	def printwelcome(self):
		"""
		Vypíše uvítací zprávu.
		:return:
		"""
		clean()
		mezera()
		print('\n \nBuď zdráv člověče, mAG-Bot ver.0.1.1 se nahrává... \n')

	def printReady(self):
		print('mAG-Bot ver.0.1.1 startuje.\n')
		print("\n")
		print("Obchodování začne: ", self.starttradingtime)
		print("\n")
		tenkamezera()

	def starttradingsignalsloading(self):
		clean()
		print("\n\nMinimum candlesticků pro výpočty indikátorů bylo právě nahráno.\n")
		print("Začínám stavět signály indikátorů.\n")
		print("Dalších ", self.config.indicatorsLength, " candlesticků bude trvat zahájení obchodování.\n")
		print("Obchodování bude zahájeno v: ", self.starttradingtime)

	def printkeysmissing(self):
		clean()
		print("\n\nNENAŠEL JSEM KLÍČE API A SECRET.!"
		      "\nPROSÍM DOPLŇTE POTŘEBNÉ INFORMACE.!\n \n")

	def printshortcandleserror(self):
		print("Došlo v vyvolání třídy FillIndicators, modulu 'Decisions.py',"
		      "aniž bychom měli candlesticky požadované délky.")

	def printshortemacandleserror(self):
		print("Data pro emy indikátorů nejsou dostatečně dlouhá.\n ")

	def printKill(self):
		print("\n \n \nTeď jsi mě zabil... \n \n \n")


class TraderPrinter:
	"""
	Tato třída tiskne výstup z modulu
	Trader.py.
	"""

	def __init__(self):
		pass

	def printTrader(self, simulation, startedtime, currenttime, usdinitialfunds, initialfunds, currentfunds, buys,
	                sells,
	                losses, profits, currentinusdfunds):
		"""
		Vytiskne do terminálu stav obchodování.
		:param startedtime:
		:param usdinitialfunds:
		:param initialfunds:
		:param currentfunds:
		:param buys:
		:param sells:
		:param losses:
		:param profits:
		:param currentinusdfunds:
		:return:
		"""
		procent = (currentinusdfunds - usdinitialfunds) / (usdinitialfunds / 100)
		if profits:
			tradesprocent = procent / profits
		else:
			tradesprocent = 0.0
		clean()
		mezera()
		if simulation:
			print("mAG_BOt je spuštěn na simulaci.")
		else:
			print("mAG_BOt je spuštěn na reálné obchodování.")
		print("Čas počátku obchodování byl: ", startedtime)
		print("Stav financí na počátku byl: ", initialfunds)
		tenkamezera()
		print("Čas tohoto výstupu do terminálu: ", currenttime)
		print("Stav financí je: ", currentfunds)
		print("Stav financí v USD je: ", currentinusdfunds)
		print("Počet nákupů: ", buys)
		print("Počet prodejů: ", sells)
		print("Počet výdělečných obchodů je: ", profits)
		print("Počet prodělečných obchodů je: ", losses)
		tenkamezera()
		print("Celková procentuální úspěšnost je: ", procent, "%.")
		print("Procentuální úspěšnost je ", tradesprocent, "% na každý výdělečný obchod.")
		mezera()


class DataCollectingPrinter:
	"""
	Tato třída tiskne výstup z modulu
	Trader.py.
	"""

	def __init__(self):
		pass

	def printDataColecting(self, candlesticklength, tickerfrequency, candlescounter):
		clean()
		mezera()
		print("mAG_BOt je spuštěn na sběr dat.")
		tenkamezera()
		print("Délka jednoho candlesticku je ", int(candlesticklength), " sec.")
		print("Frekvence tickerů je ", tickerfrequency, " sec.")
		tenkamezera()
		print("Čas posledního přidání candlesticku byl: ", str(time.asctime()))
		print("Počet candlesticků je: ", candlescounter)
		mezera()


####################
#
####################


# Testy:
if __name__ == "__main__":
	# Funkce
	def mezera():
		print("#" * 70)


	def clean():
		print("\n" * 50)


	tp = TraderPrinter()
