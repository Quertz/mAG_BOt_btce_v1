#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import Helper


"""
Tento modul má na starost omezení ztrátových obchodů. V případě
třídy LosingTradeStopper(), se jedná o odfiltrování prodejů, u
obchodů, které si ještě nevidělali ani na poplatky. V případě třídy
LosingStrategyStopper(), se jedná o zastavení celého bota v případě
že dojde k prodělku a zaslání upozornění na email.
"""


# ------------
# Třídy
# ------------


class LosingTradeStopper:
	"""
	Pozastavení odprodeje pro obchod jež si ještě
	nevidělal na poplatky.
	"""

	def __init__(self):
		"""
		Inicializace nastavení, pro načtení
		výše minimálního výdělku, jež jsme určili
		v settings.ini - losingsPolicyOffset.
		"""
		self.config = Helper.Config()

	def proceedprices(self, bigdataset, boughts, pairstosell):
		"""
		Porovnáváme nákupní a prodejní ceny měny.
		Pokud jsme ještě nepokryli náklady, měna
		se nezařadí do seznamu newpairstosell a nedojde
		k odprodeji.
		:param bigdataset:
		:param boughts:
		:param pairstosell:
		:return:
		"""
		newpairstosell = []

		def retrievecurrrentprice4pairs2sell(pair):
			"""
			Vrátí nejaktuálnější cenu pro zadaný pár,
			tak jak se vyskytuje v datasetu.
			:param pair:
			:return:
			"""
			price = None
			for i in bigdataset:
				for k, v in i.items():
					if k == "pair" and v == pair:
						prices = list(i["avg_price"])
						prices = list(reversed(prices))
						price = prices[0]
						return float(price)

		def getBougthpairs():
			"""
			Navrací seznam nekoupených měnových párů.
			:return:
			"""
			bougthpairs = []
			for i in boughts:
				bougthpairs.append(i["pair"])
			return bougthpairs

		# Zde odfiltrujeme páry, které nepokryli náklady.
		boughtpairs = getBougthpairs()
		for pair in pairstosell:
			if pair in boughtpairs:
				currprice = retrievecurrrentprice4pairs2sell(pair)
				buyprice = None
				for n in boughts:
					if n["pair"] == pair:
						buyprice = n["price"]
				offfsetprice = float(buyprice + ((buyprice / 100) * self.config.losingsPolicyOffset))
				if currprice > offfsetprice:
					newpairstosell.append(pair)
		return newpairstosell


class LosingStrategyStopper:
	"""
	Tato třída má za úkol hlídat výši
	celkového prodělku a když překročí
	výši offsetu, tak jak je v nastavení
	bot se vypne a zašle na email varovnou zprávu.
	"""

	# TODO: Dodělat tento mechanismus.
	def __init__(self):
		pass
