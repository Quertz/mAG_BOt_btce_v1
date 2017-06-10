#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import os
import sys
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import listdir
from os.path import isfile, join
import time
import Helper


"""
Tento modul má na starosti zasílání
emailů a zpráv na zvolenou emailovou adresu.
"""

# ------------
# Konstanty
# ------------

NL = "\n"
PAIRSDATABASE = "./0_databases/pairsinfo.db"
CANDLESDATABASE = "./0_databases/candles.db"
SIGNALSDATABASE = "./0_databases/indicators.db"


# ------------
# Třídy
# ------------

class Mailer:
	def __init__(self):
		self.config = Helper.Config()
		self.sender = self.config.sender
		self.senderspassword = self.config.sendersPassword
		self.recepient = self.config.recepient
		self.counter = 0
		# Délku candlesticků chceme v minutách.
		self.candlesticklength = int(self.config.candlestickLenght / 60)
		self.tradingpairs = str(", ".join(self.config.tradingPairs))

	def atachLogs(self):
		"""
		Provede výběr souboru logování pro
		připojení k internetu.
		:return:
		"""
		logs = []
		for root, dirs, files in os.walk("../"):
			for file in files:
				if file.endswith(".log"):
					logs.append(str(os.path.join(root, file)))
		return logs

	def emailSkeleton(self, report=None, attachments=None):
		"""
		Tato metoda vytváří hlavní tělo
		a funkce pro odeslání emailu.
		:param report:
		:return:
		"""
		self.counter += 1
		# Create the enclosing (outer) message
		outer = MIMEMultipart()
		outer['Subject'] = str("Report č. " + str(self.counter) + " z " + str(self.candlesticklength) +
		                       " min. mAG_BOta pro páry: " + self.tradingpairs + ".")
		outer['To'] = self.recepient
		outer['From'] = self.sender
		outer.preamble = '...\n'
		outer.attach(MIMEText(str(report)))

		if attachments == "logs":
			attachments = self.atachLogs()

		if attachments:
			# Add the attachments to the message
			for file in attachments:
				try:
					with open(file, 'rb') as fp:
						msg = MIMEBase('application', "octet-stream")
						msg.set_payload(fp.read())
					encoders.encode_base64(msg)
					msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
					outer.attach(msg)
				except:
					print("Unable to open one of the attachments. Error: ", sys.exc_info()[0])
					# TODO: Zalogovat tuto chybu.
					pass
		composed = outer.as_string()
		# Send the email
		try:
			with smtplib.SMTP('smtp.seznam.cz', 25) as s:
				s.ehlo()
				s.starttls()
				s.ehlo()
				s.login(self.sender, self.senderspassword)
				s.sendmail(self.sender, self.recepient, composed)
				s.close()
		except:
			pass

	def reportBotBegins(self):
		t = str(time.asctime())
		text1 = "mAG-Bot ver.0.1.2 startuje."
		fulltext = str(t + NL + text1)
		self.emailSkeleton(report=fulltext)

	def reportBotEnded(self):
		t = str(time.asctime())
		text1 = "mAG-Bot ver.0.1.2 byl ukončen."
		text2 = "Připojil jsem logy běhu programu."
		fulltext = str(t + NL + text1 + NL + text2)
		self.emailSkeleton(report=fulltext, attachments="logs")

	def reportNetworkConnectionError(self):
		t = str(time.asctime())
		missingcandlesamount = str(int(self.config.missingCandlesLength) *
		                           int(self.config.candlestickLenght))
		text1 = "MAG-Bot varování."
		text2 = "Došlo k výpadku sítě po dobu delší než "
		text3 = " minut."
		text4 = "Bot doplňuje do databází poslední známá data, s nulovými volumy."
		fulltext = str(t + NL + text1 + NL + text2 + missingcandlesamount + text3 + NL + text4)
		self.emailSkeleton(report=fulltext)

	def reportNetworkStableReconnection(self):
		t = str(time.asctime())
		missingcandlesamount = str(int(self.config.missingCandlesLength) *
		                           int(self.config.candlestickLenght))
		text1 = "MAG-Bot upozornění."
		text2 = "Síť je již stabilní po dobu delší "
		text3 = " minut."
		text4 = "Síť je považována za stabilní."
		fulltext = str(t + NL + text1 + NL + text2 + missingcandlesamount + text3 + NL + text4)
		self.emailSkeleton(report=fulltext)

	def reportTrade(self, startedtime, currenttime, usdinitialfunds, initialfunds, currentfunds, buys,
	                sells, losses, profits, currentinusdfunds):
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
		linka = str("~" * 50 + "\n")
		text0 = str("\nProvedl jsem další kompletní obchod. \nVypisuji bilanci: \n \n")
		text1 = str("Čas tohoto výpisu je:: " + str(currenttime))
		text2 = str("Čas počátku obchodování byl: " + str(startedtime))
		text3 = str("Stav financí na počátku byl: " + str(initialfunds))
		text4 = str("Stav financí je: " + str(currentfunds))
		text5 = str("Stav financí v USD je: " + str(currentinusdfunds))
		text6 = str("Počet nákupů: " + str(buys))
		text7 = str("Počet prodejů: " + str(sells))
		text8 = str("Počet výdělečných obchodů je: " + str(profits))
		text9 = str("Počet prodělečných obchodů je: " + str(losses))
		text10 = str("Celková procentuální úspěšnost je: " + str(procent) + "%.")
		text11 = str("Procentuální úspěšnost je " + str(tradesprocent) + "% na každý výdělečný obchod.")

		fulltext = str(linka + text0 + linka + NL + text1 + NL + text2 + NL + text3 + NL + text4 + NL
		               + text5 + NL + text6 + NL + text7 + NL + text8 + NL
		               + text9 + NL + text10 + NL + text11 + NL + linka)

		self.emailSkeleton(report=fulltext)


# ------------
# Testy
# ------------

if __name__ == "__main__":
	# Funkce
	def mezera():
		print("#" * 70)


	def clean():
		print("\n" * 50)


	# Přiřazení instancí tříd
	t = Mailer()
	# Přiřazení metods

	# Výstup
	t.reportTrade("12:35", "16:56", 154, 12, 25, 6, 5, 1, 4, 654)
