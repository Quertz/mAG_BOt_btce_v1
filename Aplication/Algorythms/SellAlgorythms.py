#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import Helper


"""
Tento modul obsahuje pouze třídy, jež ze zadané posloupnosti dat
vyhodnocují, zda je pár vhodný k prodeji. Zadaným argumentem je
posloupnost s daty o jednom měnovém páru. Návratovou hodnotou je
slovník s dvojicemi dat, názvem páru, pak názvem oscilátoru jako
klíčem a booleanovskou hodnotou jako hodnotou True pro sell a False
pro not sell.
"""


# ------------
# Třídy
# ------------


class Methods4SellAlgorythms:
	"""
	Pokud se indikátor
	vyskytuje ve více metodách, standartně
	první metoda v třídě je nejotevřenější
	a nejbenevolentnější a postupně s každou další
	metodou je přísnější a přísnější.

	Existují různé stupně indikátorů,
	jejich předpony se mohou i kombinovat:

	Opened:     je nejbenevolentnější a nejotevřenější nastavení indikátoru.
	Simple:     je jednoduché nastavení indikátoru.
	Rigorous:   je přísné nastavení indikátoru.
	Sensitive:  je nastavení zhruba na úrovni simple, ale se senzitivnějšími výpočty,
				které většinou zahrnují zprůměrování za úsek cca 3 či 4 candlesticky.
	"""

	def __init__(self):
		self.config = Helper.Config()

	# Navrátí pár z datasetu:

	def GetPair(self, dataset):
		"""
		Získá pár z datasetu.
		:param dataset:
		:return:
		"""
		pair = None
		for key, value in dataset.items():
			if key == "pair":
				pair = value
		return pair

	# Trend trhu:

	def MarketTrend(self, dataset):
		"""
		Stabilita a trend trhu.
		:param dataset:
		:return:
		"""

		def getData():
			datatrimaslow = None
			for key, value in dataset.items():
				if key == "trimaultraslow":
					datatrimaslow = list(value)
			return datatrimaslow

		datatrimaslow = getData()
		if datatrimaslow[-3] > datatrimaslow[-2] > datatrimaslow[-1]:
			sell = True
		else:
			sell = False
		return sell

	# Trima:

	def FullyFallingTrima(self, dataset):
		"""
		Výpočet čistě jen na pohyb trimy slow.
		:param dataset:
		:return:
		"""
		trimaultrafastdata = []
		trimafastdata = []
		trimaslowdata = []
		for key, value in dataset.items():
			if key == "trimaultrafast":
				trimaultrafastdata = list(reversed(value))
		for key, value in dataset.items():
			if key == "trimafast":
				trimafastdata = list(reversed(value))
		for key, value in dataset.items():
			if key == "trimaslow":
				trimaslowdata = list(reversed(value))

		if trimaultrafastdata[0] < trimafastdata[0] < trimaslowdata[0]:
			sell = True
		else:
			sell = False
		return sell

	# RSI:

	# Stochastic:

	# Macd:

	# AD:

	def AdEma(self, dataset):
		"""
		Zpracování ad signálů.
		Používáme převrácenou logiku,
		abychom zjistili zda každý člen
		v posloupnosti má dané vlastnosti.
		:param dataset:
		:return:
		"""
		ademadata = []
		sell = True
		for key, value in dataset.items():
			if key == "adema":
				ademadata = list(value)
		ademadata = list(reversed(ademadata))
		ademadata = ademadata[:1]
		for i in ademadata:
			if i > 0.0:
				sell = False
		return sell

	def VolatileAdEma(self, dataset):
		"""
		Zpracování ad signálů.
		Používáme převrácenou logiku,
		abychom zjistili zda každý člen
		v posloupnosti má dané vlastnosti.
		:param dataset:
		:return:
		"""
		ademadata = []
		addata = []
		sell = False
		nsell = False
		asell = None
		for key, value in dataset.items():
			if key == "adema":
				ademadata = list(reversed(value))
		for key, value in dataset.items():
			if key == "ad":
				addata = list(reversed(value))
		if ademadata[0] < 0.0 and ademadata[1] < 0.0:
			sell = True
		if addata[0] < 0.0 and addata[1] < 0.0 and addata[2] < 0.0:
			nsell = True
		if sell and nsell:
			asell = True
		else:
			asell = False
		return asell

	# Bop:

	# Mom:

	def MomEma(self, dataset):
		"""
		Jednoduchý výpočet pro mom.
		:param dataset:
		:return:
		"""
		momdata = []
		for key, value in dataset.items():
			if key == "momema":
				momdata = list(value)
		momdata = list(reversed(momdata))
		if momdata[0] < momdata[1] < momdata[2]:
			sell = True
		else:
			sell = False
		return sell

	# Volumes:

	def Volumes(self, dataset):
		"""
		Sensitivní výpočet pro mom.
		:param dataset:
		:return:
		"""
		voldata = []
		for key, value in dataset.items():
			if key == "volumes":
				voldata = list(reversed(value))
		if voldata[0] > voldata[1]:
			buy = True
		else:
			buy = False
		return buy


class SellAlgorythms:
	"""
	Tato třídy obsahuje algorytmy, pro vyhodnocování
	prodeje.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.sellmethods = Methods4SellAlgorythms()
		self.dataset = None

	# První Algorytmus:
	def FirstAlgorythm(self, dataset):
		"""
		Tato metoda provede všechna vyhodnocení.
		:param dataset:
		:return:
		"""
		self.dataset = dataset

		pairdict = {}
		pairdict["pair"] = self.sellmethods.GetPair(self.dataset)
		pairdict["adema"] = self.sellmethods.AdEma(self.dataset)
		pairdict["market"] = self.sellmethods.MarketTrend(self.dataset)
		return pairdict

	# Druhý Algorytmus:
	def SecondAlgorythm(self, dataset):
		"""
		Tato metoda provede všechna vyhodnocení.
		:param dataset:
		:return:
		"""
		self.dataset = dataset

		pairdict = {}
		pairdict["pair"] = self.sellmethods.GetPair(self.dataset)
		pairdict["bop"] = self.sellmethods.VolatileAdEma(self.dataset)
		pairdict["trima"] = self.sellmethods.FullyFallingTrima(self.dataset)

		return pairdict
