#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import sqlite3
import BuyAlgorythms
import SellAlgorythms
import Helper
import PricePolicy
import LosingsPolicy
import SequencialBuying


"""
Tento modul má na starost zpracování dat,
jež obdrží metoda applyAll(), třídy AllDecisionsAndStrategies().
Ta vyvolá třídy BuyDecisions() a SellDecisions(), které vyvolávají
jednotlivé algorytmy a navracejí rozhodnutí k prodeji či nákupu.
Bigdataset je seznam jednoduchých slovníků, informací o
párech. Viz:
[
{pair:"btc_usd", macd:55.4568, ...},
{pair:"ltc_usd", macd:25.1112, ...},
...
]
"""


# ------------
# Třídy
# ------------


class BuyDecisions:
	"""
	Třída jež rozhoduje o nákupech.
	Data vyzíská z předaného argumentu 'bigdataset'
	a pro vyhodnocení použije algorytmy z modulu -
	BuyAlgorythms.py.
	"""

	def __init__(self):
		self.buyalgorythm = BuyAlgorythms.BuyAlgorythms()
		self.config = Helper.Config()
		self.usefirstalgorythm = bool(self.config.usefirstalgorythm)
		self.usesecondalgorythm = bool(self.config.usesecondalgorythm)


	# Toto je zpracování pro první nákupní algorytmus.
	def firstalgorythmproceed(self, bigdataset):
		"""
		Tato metoda zpracuje a podá výsledky pro
		první nákupní algorytmus.
		:param bigdataset:
		:return:
		"""
		allpairs2buy = []

		def proceedresults(pairdataset):
			"""
			Zpracuje výsledky které se navrátíli
			po zpracování dat, v předchozí třídě.
			:param pairdataset:
			:return:
			"""
			singlepairdataset = self.buyalgorythm.FirstAlgorythm(pairdataset)
			# Zde vyhodnocujeme a řadíme jednotlivé boolean hodnoty,
			# pro zadaný pár.
			if singlepairdataset["natr"]:
				if singlepairdataset["rsiema"]:
					if singlepairdataset["adema"]:
						if singlepairdataset["trima"]:
							if singlepairdataset["volumes"]:
								# Pokud jsme splnili všechny podmínky, zařadíme měnu
								# do seznamu na nákup.
								newdict = {
									"pair": singlepairdataset["pair"],
									"price": singlepairdataset["price"]
								}
								allpairs2buy.append(newdict)
								return True

		def allvariablesproceed(bigdataset):
			"""
			Zpracuje data jednotlivých párů z posloupností dat
			v 'bigdataset'.
			:param bigdataset:
			:return:
			"""
			# Zde zpracováváme jednotlivé datasety.
			for pairdataset in bigdataset:
				proceedresults(pairdataset)

		allvariablesproceed(bigdataset)
		return allpairs2buy

	# Toto je zpracování pro druhý nákupní algorytmus.
	def secondalgorythmproceed(self, bigdataset):
		"""
		Tato metoda zpracuje a podá výsledky pro
		první nákupní algorytmus.
		:param bigdataset:
		:return:
		"""
		allpairs2buy = []

		def proceedresults(pairdataset):
			"""
			Zpracuje výsledky které se navrátíli
			po zpracování dat, v předchozí třídě.
			:param pairdataset:
			:return:
			"""
			singlepairdataset = self.buyalgorythm.SecondAlgorythm(pairdataset)
			# Zde vyhodnocujeme a řadíme jednotlivé boolean hodnoty,
			# pro zadaný pár.
			if singlepairdataset["market"]:
				if singlepairdataset["volume"]:
					if singlepairdataset["ad"]:
						if singlepairdataset["macd"]:
							# Pokud jsme splnili všechny podmínky, zařadíme měnu
							# do seznamu na nákup.
							newdict = {
								"pair": singlepairdataset["pair"],
								"price": singlepairdataset["price"]
							}
							allpairs2buy.append(newdict)
						return True

		def allvariablesproceed(bigdataset):
			"""
			Zpracuje data jednotlivých párů z posloupností dat
			v 'bigdataset'.
			:param bigdataset:
			:return:
			"""
			# Zde zpracováváme jednotlivé datasety.
			for pairdataset in bigdataset:
				proceedresults(pairdataset)

		allvariablesproceed(bigdataset)
		return allpairs2buy

	def allbuyalgorythmsproceed(self, bigdataset):
		"""
		Tato metoda sjednotí zpracování
		všech algorytmů a navrátí výsledky.
		:param bigdataset:
		"""
		allresults = []
		# Zavádíme nastavení na použití algorytmů:
		if self.usefirstalgorythm:
			firstalgoresult = self.firstalgorythmproceed(bigdataset)
		else:
			firstalgoresult = []
		if self.usesecondalgorythm:
			secondalgoresult = self.secondalgorythmproceed(bigdataset)
		else:
			secondalgoresult = []

		# Přiřazujeme čísla algorytmů:
		if firstalgoresult:
			for i in firstalgoresult:
				newdict = {"algorythm": int(1)}
				i.update(newdict)
				allresults.append(i)
		if secondalgoresult:
			for i in secondalgoresult:
				newdict = {"algorythm": int(2)}
				i.update(newdict)
				allresults.append(i)
		return allresults


class SellDecisions:
	"""
	Třída jež rozhoduje o nákupech.
	Data vyzíská z předaného argumentu 'bigdataset'
	a pro vyhodnocení použije algorytmy z modulu -
	SellAlgorythms.py.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.sellalgorythms = SellAlgorythms.SellAlgorythms()
		self.usefirstalgorythm = bool(self.config.usefirstalgorythm)
		self.usesecondalgorythm = bool(self.config.usesecondalgorythm)

	# Toto je zpracování pro první prodejní algorytmus.
	def firstalgorythmproceed(self, bigdataset):
		"""
		Získává seznam pokynů k nákupu z předchozí funkce.
		Udržuje jej, aktualizuje a navrací seznam měn k nákupu.
		:param bigdataset:
		:return:
		"""
		allpairs2sell = list()

		def proceedresults(singlepairdataset):
			"""
			Tato funkce zajístí návrat výsledku z modulu
			SellAlgorythms.py a jeho zpracování.
			:param singlepairdataset:
			:return:
			"""
			result = dict(self.sellalgorythms.FirstAlgorythm(singlepairdataset))
			# Zde vyhodnocujeme a řadíme jednotlivé
			# boolean hodnoty, pro každý pár.
			# K seznamu pro čekání připojujeme
			# až po splnění první podmínky.
			if result["adema"]:
				if result["market"]:
					# Pokud jsme splnili všechny podmínky,
					# zařadíme měnu do seznamu na nákup.
					allpairs2sell.append(result["pair"])
					return True

		def allvariablesproceed(bigdataset):
			"""
			Zpracuje data jednotlivých párů z posloupností dat
			v 'bigdataset'.
			:param bigdataset:
			:return:
			"""
			# Zde zpracováváme jednotlivé datasety.
			for pairdataset in bigdataset:
				proceedresults(pairdataset)

		allvariablesproceed(bigdataset)
		return allpairs2sell

	# Toto je zpracování pro druhý prodejní algorytmus.
	def secondalgorythmproceed(self, bigdataset):
		"""
		Získává seznam pokynů k nákupu z předchozí funkce.
		Udržuje jej, aktualizuje a navrací seznam měn k nákupu.
		:param bigdataset:
		:return:
		"""
		allpairs2sell = list()

		def proceedresults(singlepairdataset):
			"""
			Tato funkce zajístí návrat výsledku z modulu
			SellAlgorythms.py a jeho zpracování.
			:param singlepairdataset:
			:return:
			"""
			result = dict(self.sellalgorythms.SecondAlgorythm(singlepairdataset))
			# Zde vyhodnocujeme a řadíme jednotlivé
			# boolean hodnoty, pro každý pár.
			# K seznamu pro čekání připojujeme
			# až po splnění první podmínky.
			if result["bop"]:
				if result["trima"]:
					# Pokud jsme splnili všechny podmínky,
					# zařadíme měnu do seznamu na nákup.
					allpairs2sell.append(result["pair"])
					return True

		def allvariablesproceed(bigdataset):
			"""
			Zpracuje data jednotlivých párů z posloupností dat
			v 'bigdataset'.
			:param bigdataset:
			:return:
			"""
			# Zde zpracováváme jednotlivé datasety.
			for pairdataset in bigdataset:
				proceedresults(pairdataset)

		allvariablesproceed(bigdataset)
		return allpairs2sell

	def allsellalgorythmsproceed(self, bigdataset):
		"""
		Tato metoda sjednotí zpracování
		všech algorytmů a navrátí výsledky.
		:param bigdataset:
		"""
		allresults = []
		# Zavádíme nastavení na použití algorytmů:
		if self.usefirstalgorythm:
			firstalgoresult = self.firstalgorythmproceed(bigdataset)
		else:
			firstalgoresult = []
		if self.usesecondalgorythm:
			secondalgoresult = self.secondalgorythmproceed(bigdataset)
		else:
			secondalgoresult = []

		# Přiřazujeme čísla algorytmů:
		if firstalgoresult:
			for i in firstalgoresult:
				newdict = {}
				newdict = {"pair": str(i), "algorythm": int(1)}
				allresults.append(newdict)
		if secondalgoresult:
			for i in secondalgoresult:
				newdict = {"pair": str(i), "algorythm": int(2)}
				allresults.append(newdict)
		return allresults


class AllDecisionsAndStrategies:
	"""
	Zpracuje nákupní a prodejní strategie a
	zavede kontrolní a strategické mechanismy.
	"""

	# TODO: Podívat se na realtimepricepolicy. Zdá se že nefunguje.

	def __init__(self):
		self.config = Helper.Config()
		self.buydecisions = BuyDecisions()
		self.selldecisions = SellDecisions()
		self.pricepolicy = PricePolicy.CandlesticksPricePolicy()
		self.losingspolicy = LosingsPolicy.LosingTradeStopper()
		self.sequencial = SequencialBuying.SequencialProceed()
		self.buyscache = []
		self.pricepolicysells = []

	def applyAll(self, bigdataset, tradingpairs, boughts):
		"""
		Aplikuje všechny strategie a uplatní
		všechny algorytmy.
		Bigdataset je seznam jednoduchých slovníků, informací o
		párech. Viz:
		[
		{pair:"btc_usd", macd:55.4568, ...},
		{pair:"ltc_usd", macd:25.1112, ...},
		...
		]
		"""
		# Nejdříve získáme obchody ke zpracování:
		buys = self.buydecisions.allbuyalgorythmsproceed(bigdataset)
		sells = self.selldecisions.allsellalgorythmsproceed(bigdataset)
		results = []

		# Vyextrahujeme páru určené k prodeji:
		def getcurrsells():
			"""
			Navrací seznam párů, již
			určených k prodeji.
			:return:
			"""
			pairs = []
			for i in sells:
				pairs.append(i["pair"])
			return pairs

		# Zavedeme synchronizaci algorytmů:
		def synchronizeAlgorythms():
			"""
			Kompletně zpracuje synchronizaci algorytmů.
			Aktualizuje cache pro nákupy.
			Odstraňuje z pokynů k prodeji, pokyny od
			jiných algorytmů, než těch co byly použity
			k nákupům.
			Navrací nový seznam párů pro odprodej.
			"""

			def addBuysToCache():
				"""
				Přidání nákupu do cache:
				:return:
				"""
				if buys:
					for i in buys:
						newdict = {"algorythm": i["algorythm"], "pair": i["pair"]}
						if newdict not in self.buyscache:
							self.buyscache.append(newdict)

			def removeBuysFromCache():
				"""
				Odebrání nákupu z cache,
				pokud jsme obdrželi pokyn k prodeji:
				"""
				if sells:
					for i in sells:
						newdict = {"algorythm": i["algorythm"], "pair": i["pair"]}
						if newdict in self.buyscache:
							self.buyscache.remove(newdict)

			def filterOutWrongAlgorythms():
				"""
				Následující kód je platný jen při využití více algorytmů.
				Odstraňuje z doporučení k prodeji doporučení od jiného algorytmu,
				než byl použit k nákupu.
				"""
				# TODO: Zkontrolovat platnost tohoto řešení:
				# páry v cache nákupů:
				cachedpairs = [x["pair"] for x in self.buyscache]
				# pro každou položku v prodejích:
				for x in sells:
					# pokud je položka v nakoupených párech
					if x["pair"] in cachedpairs:
						# odstraň položku z prodejů
						sells.remove(x)

			# Vyvoláváme funkce:
			addBuysToCache()
			removeBuysFromCache()
			filterOutWrongAlgorythms()
			return True

		# Nyní zkontrolujeme pokyny k prodeji pomocí LosingsPolicy.
		def applylossingspolicy():
			currentsells = getcurrsells()
			newsells = self.losingspolicy.proceedprices(bigdataset, boughts, currentsells)
			for i in sells:
				if i["pair"] not in newsells:
					sells.remove(i)

		# Nyní zavedeme price policy.
		def applypricepolicy():
			"""
			Aplikuje cenovou politiku.
			:return:
			"""
			currentsells = getcurrsells()
			pricepolicysells = self.pricepolicy.proceedprices(bigdataset, boughts)
			if pricepolicysells:
				for i in pricepolicysells:
					if i not in currentsells:
						nextdict = {
							"pair": i,
							"algorythm": 0
						}
						sells.append(nextdict)
						# uvolňujeme cache,
						# pokud dochází k prodeji
						# pomocí pricepolicy:
						for s in self.buyscache:
							if s["pair"] == i:
								self.buyscache.remove(s)

		if self.config.useLosingsPolicy:
			applylossingspolicy()

			synchronizeAlgorythms()

		if self.config.useLosingsPolicy:
			applylossingspolicy()

		if self.config.usePricePolicy:
			applypricepolicy()

		buys = self.sequencial.SequentialBuysManager(sells, buys)

		results.append(buys)
		results.append(sells)
		return results
