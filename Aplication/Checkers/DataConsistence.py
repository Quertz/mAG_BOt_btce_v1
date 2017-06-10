#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com


import os
import signal
import sys
import time
import Helper
import Mailer


# ------------
# Konstanty
# ------------


PAIRSDATABASE = "./0_databases/pairsinfo.db"
CANDLESDATABASE = "./0_databases/candles.db"
SIGNALSDATABASE = "./0_databases/indicators.db"
TRADEPERMISSIONSFILE = "./0_temporary/tradespermissions.per"


# ------------
# Třídy
# ------------

class CheckConsistence:
	"""
	Třída která má na starost kontrolu,
	konzistenci candlesticků. Pokud dojde
	k DDOS útoku na směnárnu a ta nám neodpovídá na požadavky,
	pokud tato mezera v datech dosáhne určité úrovně,
	program vyčká na opětovné stabilní připojení a
	po té se restartuje.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.mailer = Mailer.Mailer()
		# Stav spojení.
		self.emergencystate = False
		# Hranice chybějících candlesticků pro vypnutí bota.
		self.missingoffset = int(self.config.missingCandlesLength)
		# Počítadlo chybějících candlesticků.
		self.missingcandlescounter = 0

	def alowTrades(self):
		fobj = open(TRADEPERMISSIONSFILE, "w", encoding="UTF-8")
		fobj.write("True")
		fobj.close()

	def denyTrades(self):
		fobj = open(TRADEPERMISSIONSFILE, "w", encoding="UTF-8")
		fobj.write("False")
		fobj.close()

	def checkconsistence(self):
		"""
		Kontroluje konzistenci dat
		a v případě jejich nekonzistentnosti
		vyvolává další mechanismy, které
		povedou k řádnému restartu aplikace.
		:return:
		"""
		if self.missingcandlescounter < 0:
			self.missingcandlescounter = 0
		if self.missingcandlescounter == self.missingoffset and not self.emergencystate:
			self.emergencystate = True
			self.mailer.reportNetworkConnectionError()
			self.denyTrades()
		elif self.missingcandlescounter > self.missingoffset:
			self.missingcandlescounter = self.missingoffset
		if self.missingcandlescounter == 0 and self.emergencystate:
			self.emergencystate = False
			self.mailer.reportNetworkStableReconnection()
			self.alowTrades()
