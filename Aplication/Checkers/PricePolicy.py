#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import Helper
import Api
import Tapi
import sqlite3


"""
Tento modul má na starosti kontrolu poklesu ceny nakoupené
měny. Pokud, pokles přesáhne offset nastavený v settings.ini,
dojde k okamžitému odprodeji měny. Zde vytváříme kontrolu
ztrát.

Po nákupu můžeme mít 4 následující stavy:
	- nárůst
	- pokles
	- pokles-nárůst
	- nárůst-pokles

	Přičemž PricePolicy řeší 3 z těchto stavů a to jsou: pokles, pokles-nárůst
	a nárůst-pokles.
	- pokles:
	    Zde je to jasné. Při okamžitém poklesu se řídíme výší
	    možné ztráty, tak jak je nastavena v pricePolicyBottomOffset.
	- pokles-nárůst:
		Zde je situace také celkem jasná.
		Pokud pokles přesáhne pricePolicyBottomOffset,
		dojde k odprodeji, pokud ne, měnu držíme.
	- nárůst-pokles:
		Zde se situace poměrně komplikuje.

		nc = nákupní cena
		pnc = 1% z nákupní ceny
		sc = současná cena
		vc = prozatím nejvyšší cena
		d = Výše nárůstu bez pricePolicyBottomOffset
		vzorec:
		d = vc - (pricePolicyBottomOffset*pnc)
		ztrata = nc+((d-nc)/2) if ztrata < pricePolicyRoofOffset else ztrata = pricePolicyRoofOffset.
		Vysvětlení:
		Dokud nárůst nepřesáhne hodnotu pricePolicyBottomOffset v
		pozitivním směru, povolená ztráta = pricePolicyBottomOffset.
		Po přesáhnutí této hranice se k pricePolicyBottomOffset připočítává
		výše nárůstu, bez pricePolicyBottomOffset děleno dvěma až po
		výši pricePolicyRoofOffset.

		tj. Výše nárůstu bez pricePolicyBottomOffset:
		d = vc - (pricePolicyBottomOffset*pnc)
"""

# TODO: Zatím neimplementuju třídu RealtimePricePolicy(), abych se vyhnul nebezpečí prodeje, při náhlém a chvilkovém
# TODO: propadu ceny. Je potřeba tenhle problém promyslet i pro prodeje jako takové.


PAIRSDATABASE = "./0_databases/pairsinfo.db"
CANDLESDATABASE = "./0_databases/candles.db"
INDICATORSDATABASE = "./0_databases/indicators.db"
SIGNALSDATABASE = "./0_databases/signals.db"
TICKERSDATABASE = "./0_databases/tickers.db"
TRADEPERMISSIONSFILE = "./0_temporary/tradespermissions.per"


# ------------
# Třídy
# ------------


class CandlesticksPricePolicy:
	def __init__(self):
		self.config = Helper.Config()
		self.pricePolicyRoofOffset = - float(self.config.pricePolicyRoofOffset)
		self.pricePolicyBottomOffset = - float(self.config.pricePolicyBottomOffset)
		self.pricePolicyRoofOffsetReference = float(self.config.pricePolicyRoofOffset)
		self.pricePolicyBottomOffsetReference = float(self.config.pricePolicyBottomOffset)
		self.tops = []

	def proceedprices(self, bigdataset, boughts):
		"""
		Zprocesuje aktuální ceny nakoupených párů.
		Pokud je cena vyšší než v předchozím kole,
		pak navýší nové high pro daný pár, pokud je
		nižší o více procent, než je povoleno v nastavení
		pak je pár odprodán.
		:param bigdataset:
		:param boughts:
		:return:
		"""
		pairs2sell = []

		def getboughtpairs():
			"""
			Z proměnné boughts získá zobchodované páry.
			:return:
			"""
			pairs = []
			if boughts:
				for i in boughts:
					for key, value in i.items():
						if key == "pair":
							pairs.append(value)
			return pairs

		def gettoppairs():
			"""
			Z proměnné self.tops získá páry,
			u nichž vedeme nejvyšší cenu.
			:return:
			"""
			pairs = []
			if self.tops:
				for i in self.tops:
					for key, value in i.items():
						if key == "pair":
							pairs.append(value)
			return pairs

		def retrievecurrrentprices(pair):
			"""
			Navrací seznam současných cen.
			Reversovaný tak, aby první člen,
			byl zároveň tím nejaktuálnějším.
			:param pair:
			:return:
			"""
			for i in bigdataset:
				for k, v in i.items():
					if k == "pair" and v == pair:
						prices = list(i["avg_price"])
						return reversed(prices)

		def updatetoppedpairs():
			"""
			Má na starost přidání a odebrání nových
			párů do proměnné self.tops.
			:return:
			"""
			boughtpairs = getboughtpairs()
			toppedepairs = gettoppairs()
			# Pokud je pár nový, zde ho přidám do seznamu
			# toppedepairs.
			for pair in boughtpairs:
				if pair not in toppedepairs:
					prices = tuple(retrievecurrrentprices(pair))
					newdict = {
						"pair": pair,
						# Při aktualizaci jež proběhne v dalším bloku kódu, budu
						# aktualizovat všechny páry, proto zde používám předposlední
						# a ne poslední výřez ceny.
						"first": prices[1],
						# Zde ještě neaktualizuju, proto
						# i zde, zadávám předchozí cenu.
						"high": prices[1]
					}
					self.tops.append(newdict)
			# Pokud pár už v nakoupených párech není,
			# odstraním ho z toppedpairs.
			for pair in toppedepairs:
				if pair not in boughtpairs:
					for i in self.tops:
						for k, v in i.items():
							if k == "pair" and v == pair:
								self.tops.remove(i)

		def proceed():
			"""
			Jádro metody. Zpracovává a vyhodnocuje ceny.
			nc = nákupní cena
			pnc = 1% z nákupní ceny
			sc = současná cena
			vc = prozatím nejvyšší cena
			d = Výše nárůstu bez pricePolicyBottomOffset
			vzorec:
			d = vc - (pricePolicyBottomOffset*pnc)
			ztrata = nc+((d-nc)/2) if ztrata < pricePolicyRoofOffset else ztrata = pricePolicyRoofOffset.
			:return:
			"""
			# Vlastní zpracování nakoupených párů.
			for i in self.tops:
				pair = i["pair"]
				nc = float(i["first"])
				pnc = float(nc / 100)
				vc = i["high"]
				prices = tuple(retrievecurrrentprices(pair))
				sc = prices[0]
				d = None
				if sc >= vc:
					newdict = {
						"pair": pair,
						"first": nc,
						"high": vc
					}
					i.update(newdict)
				else:
					# Pokud vůbec nedošlo k nárůstu nebo došlo
					# k nárůstu jen v rámci nc + (PPBottom * pnc):
					if vc <= float(nc + (self.pricePolicyBottomOffsetReference * pnc)):
						# Pak kontrolujeme, zda pokles je větší než v nastavení
						# pro PPBottom. PPBottom protože jsme na začátku a nedošlo k žádnému vraznému
						# nárůstu.
						if sc < nc - (self.pricePolicyBottomOffsetReference * pnc):
							print("Odprodej pomocí PP 1.případ pro pár: " + str(pair) + "\n"
							                                                            "Nákupní cena je: " + str(
								nc) + ".\n"
							          "Současná cena je: " + str(sc) + ".\n")
							# Pak přiřazujeme pár k odprodeji:
							pairs2sell.append(pair)
							self.tops.remove(i)
						else:
							pass
					# Pokud je ale nejvyšší dosažená cena vyšší než offset pro dno:
					else:
						zt = None
						ztmax = None
						ztcurrent = None
						# Vzorec pro výpočet povolené ztráty:
						# Dočasná proměnná:
						d = vc - (-int(self.pricePolicyBottomOffset) * pnc)
						# Maximální povolená ztráta
						ztmax = vc - float(-int(self.pricePolicyRoofOffset) * pnc)
						ztcurrent = nc + ((d - nc) / 2)
						# Pokud je vypočítaná ztráta větší než
						# nastavená ztráta, ztrata == nastavená ztráta.
						if ztcurrent < ztmax:
							zt = ztmax
						else:
							zt = ztcurrent
						if sc < zt:
							pairs2sell.append(pair)
							self.tops.remove(i)
							print("Odprodej pomocí 2.případ PP pro pár: " + str(pair) + "\n"
							                                                            "Nákupní cena je: " + str(
								nc) + ".\n"
							          "Současná cena je: " + str(sc) + ".\n")
				return pairs2sell

		# Nejdříve aktualizujeme seznamy, slovníků
		# s informacemi o párech.
		updatetoppedpairs()
		# A zprocesujeme:
		return proceed()


class RealtimePricePolicy:
	"""
	Tato třída má na starost price policy v reálném
	čase. To je pro případ kdy dojde ke strmému propadu
	trhu.
	"""

	def __init__(self):
		self.config = Helper.Config()
		# Pro realtimepricepolicy navyšuju offset o 0.5%.
		self.priceoffset = - float(self.config.pricePolicyOffset + 0.5)
		self.tops = []
		self.currentticker = None

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

	def proceedprices(self, boughts):
		"""
		Zprocesuje aktuální ceny nakoupených párů.
		Pokud je cena vyšší než v předchozím kole,
		pak navýší nové high pro daný pár, pokud je
		nižší o více procent, než je povoleno v nastavení
		pak je pár odprodán.
		:param bigdataset:
		:param boughts:
		:return:
		"""
		pairs2sell = []

		def getboughtpairs():
			"""
			Z proměnné boughts získá páry.
			:return:
			"""
			pairs = []
			if boughts:
				for i in boughts:
					for key, value in i.items():
						if key == "pair":
							pairs.append(value)
			return pairs

		def gettoppairs():
			"""
			Z proměnné boughts získá páry.
			:return:
			"""
			pairs = []
			if self.tops:
				for i in self.tops:
					for key, value in i.items():
						if key == "pair":
							pairs.append(value)
			return pairs

		def retrievecurrrentprices():
			con = sqlite3.connect(TICKERSDATABASE)
			cur = con.cursor()
			bigdict = {}
			for pair in self.pairsFromDatabase():
				newdict = {}
				for i in cur.execute("SELECT * FROM tickers_" + pair):
					newdict["high"] = i[0]
					newdict["low"] = i[1]
					newdict["sell"] = i[2]
					newdict["buy"] = i[3]
					newdict["avg"] = i[4]
					newdict["last"] = i[5]
					newdict["vol"] = i[6]
					newdict["vol_cur"] = i[7]
				bigdict[pair] = newdict
			con.close()
			return bigdict

		def selectpairs():
			"""
			Upraví seznamy párů. Přidá
			nové a odstraní staré.
			:return:
			"""
			boughtpairs = getboughtpairs()
			toppedepairs = gettoppairs()
			currentprices = retrievecurrrentprices()
			# Pokud je pár nový, zde ho přidám do seznamu toppedepairs.
			for pair in boughtpairs:
				currentsell = None
				for key, value in currentprices.items():
					if key == pair:
						currentsell = value["sell"]
				if pair not in toppedepairs:
					newdict = {
						"pair": pair,
						"first": currentsell,
						# Zde ještě neaktualizuju, proto
						# i zde, zadávám předchozí cenu.
						"high": currentsell
					}
					self.tops.append(newdict)
			# Pokud pár už v nakoupených párech není,
			# odstraním ho z toppedpairs.
			for pair in toppedepairs:
				if pair not in boughtpairs:
					for i in self.tops:
						for k, v in i.items():
							if k == "pair" and v == pair:
								self.tops.remove(i)
			# Navracíme současné ceny abychom nezatěžovali server:
			return currentprices

		# Nejdříve aktualizujeme seznamy, slovníků
		# s informacemi o párech.
		currprices = selectpairs()
		# Vlastní zpracování nakoupených párů.
		for i in self.tops:
			pair = i["pair"]
			first = i["first"]
			previewhigh = i["high"]
			curravg = currprices[pair]["sell"]
			if curravg > previewhigh:
				newdict = {
					"pair": pair,
					"first": first,
					"high": curravg
				}
				i.update(newdict)
			elif curravg < previewhigh:
				procento = float(first / 100)
				change = float((curravg - first) / procento)
				if change < self.priceoffset:
					newd = {
						"pair": pair,
						"algorythm": int(0)
					}
					pairs2sell.append(newd)
					self.tops.remove(i)
				else:
					pass
			else:
				pass

		return pairs2sell
