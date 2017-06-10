#!/usr/bin/env python3

import csv
import sqlite3
import time


CANDLESTICKLENGTH = 30

"""
Tento modul slouží ke konverzi dat stažených z
https://bitcoinchain.com/markets/btcusd-btce
ve formě jednominutových candlesticků, ve formátu
D_T_O_H_L_C_V do souboru btc_usd.csv.
Proto abychom co nejvěrněji simulovali trh,
použiju na sestavení 30min. candlesticků, co
nejvěrnější metodu jakou používá mag_bot.
"""


# TODO: Přepsat na minuty.


def createDatabase():
	# Create the database
	con = sqlite3.connect("./candles.db")
	cur = con.cursor()
	cur.execute(
		"CREATE TABLE IF NOT EXISTS {p}("
		"candle_ID,"
		"status,"
		"time,"
		"open,"
		"close,"
		"min,"
		"max,"
		"avg,"
		"vol,"
		"vol_currency"
		")".format(p="candlesticks_btc_usd", ))
	con.commit()


def getDataFromCsv():
	# Load the CSV file into CSV reader
	csvfile = open('./btc_usd.csv', 'r')
	creader = csv.reader(csvfile, delimiter=',', quotechar='|')
	counter = 0

	while True:
		for line in creader:
			breakpoint = counter + CANDLESTICKLENGTH
			counter += 1
			print("Počet candlesticků: ", counter)
			newlist = []
			for i in t[2:]:
				i = float(i)
				newlist.append(i)
			op = newlist[0]
			hi = newlist[1]
			lo = newlist[2]
			cl = newlist[3]
			vo = newlist[4]

		average = float((op + cl + hi + lo) / 4)
		stringquery = 'INSERT INTO candlesticks_btc_usd(candle_ID, status, time, open, close,'\
		              'min, max, avg, vol, vol_currency'\
		              ')' + ' VALUES(?,?,?,?,?,?,?,?,?,?)'
		val = (counter,
		       "real",
		       time.time(),
		       op,
		       cl,
		       lo,
		       hi,
		       average,
		       vo,
		       vo
		       )
		cur.execute(stringquery, val)
		con.commit()


def countData(data):
	"""
	Výpočetní úkony jsou implementovány zde.
	Tato funkce z candlesticků v csv vypočítá průměry,
	maxima, minima atd.
	:return list:
	"""
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


# Close the csv file, commit changes, and close the connection
csvfile.close()
con.commit()
con.close()
