#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import Helper

"""
Sequencial Buying je strategie, kdy při prvním
nákupu měny nakupujeme jen za částku, kterou
dostaneme vydělením stavu našeho účtu, pomocí
dělitele v nastavení v settings.ini, pod hlavičkou
sequencialbuying. Pro každý další dokup, musí
přijít signál od některého z algorytmů. Protože
budu přidávat nové a povlovat více nákupů stávajícím
algorytmům, není třeba se obávat nedostatečných nákupů.
Proběhlé nákupy i dokupy udržujeme v proměnném seznamu. K prodeji
dochází pokud jakkýkoliv z algorytmů dá pokyn a
odprodává se celá částka. Po té se seznam proběhlých
obchodů kompletně promaže.
"""

# Pokyny k nákupu z modulu ProceedAlgorythms.py mají tuto formu:
# Návrat pro nákup:
# [{'price': 575.952678041544, 'algorythm': 1, 'pair': 'btc_usd'}, ]
# Návrat pro prodej:
# [{'algorythm': 1, 'pair': 'btc_usd'}, ]


class SequencialProceed:
	"""
	Toto by měla být poměrně jednoduchá třída
	která mi bude udržovat proměnné o proběhlých
	obchodech. Synchronizovat algorytmy, aby se nebyly
	atd.
	"""

	def __init__(self):
		self.localboughtscache = []
		self.config = Helper.Config()
		self.sequencialbuys = int(self.config.sequencialbuying)

	def retrieveBoughtPairs(self):
		"""
		Z self.localboughtscache mi načte zakoupené páry.
		Self.localboughtscache bude mít zřejmě tuto formu:
		[{'price': 575.952678041544, 'algorythm': 1, 'pair': 'btc_usd', "sequencialbuy": 3}, ]
		:return:
		"""
		boughtpairs = []
		if self.localboughtscache:
			for i in self.localboughtscache:
				boughtpairs.append(i["pair"])
		return boughtpairs

	def SynchronizeAlgorythms(self, sells, buys):
		"""
		1.krok:
		Synchronizace algorytmů. Jedná se vzhledem k tomu, že k
		situaci, kdy mi jedem algorytmus nakupuje, ve stejný okamžik
		jako druhý prodává, by mělo docházet velice málo anebo vůbec
		spíše jen o kontrolní funkci.
		:param sells:
		:param buys:
		:return:
		"""
		# Nejdříve zajistíme, že se algorytmy vzájemně neruší, tím
		# že by mi posílali signály k nákupům i prodeji zároveň:
		if buys:
			# Pro každý pár v nákupech, pokud je pár zároveň v prodejích,
			# (K tomu by mělo dojít jen velice zřídka, pokud vůbec), se ruší
			# jeho nákup. Toto je jen kontrolní funkce.
			# Pro každý pár v pokynech k nákupu:
			for buypair in buys:
				pair2buy = buypair["pair"]
				# Všechny páry k prodeji načteme do seznamu:
				pairs2sell = []
				# Pokud máme nějaké páry k prodeji:
				if sells:
					# Přidáme je do jednoduše iterovatelného seznamu:
					for sellpair in sells:
						pairs2sell.append(sellpair["pair"])
					# Pokud je pár určený k nákupu zároveň v párech určených
					# k prodeji máme problém.
					# TODO: Tuhle situaci řádně zalogovat.
					if pair2buy in pairs2sell:
						# Odstraníme ze seznamu pokynů k nákupu,
						# všechny výskyty daného páru:
						for i in buys:
							if i["pair"] == pair2buy:
								buys.remove(i)
		return buys

	def HandleSequentialNumbers(self, buys):
		"""
		Tato funkce má na starost správu a počítání
		zbývajících možných sekvenčních dokupů.
		:return:
		"""

		if buys:
			for b in buys:
				# Zakoupené páry chceme obdržet zde, protože s každou
				# zdejší iterací se seznam zakoupených párů aktualizuje.
				boughtpairs = self.retrieveBoughtPairs()
				pair2buy = b["pair"]
				amountheight = None
				# Zde počítáme kolikrát jsme už tento pár nakoupili:
				sid = boughtpairs.count(pair2buy)
				# Zlomek vyjadřující podíl stavu účtu, který
				# použijeme na obchodování.
				# Tzn. nastavený počet dokupů - již realizované dokupy.
				amountheight = int(self.sequencialbuys - sid)
				# Pokud je amountheight, čili výše objemu USD za který nakupujeme
				# menší, než 1, znamená to že jsme všechny seqvence nákupu měny
				# vyčerpali, na účtě by už neměla zbývat žádná volná měna a my
				# můžeme výzvu k nákupu ignorovat.
				if amountheight < 1:
					# Nyní tedy vyčistíme od tohoto páru všechny pokyny
					# k nákupům.
					for m in buys:
						if m["pair"] == pair2buy:
							buys.remove(m)
				# Pokud, je ale amountheight >= 1, musíme jej zapsat do
				# lokálního seznamu nákupů a spolu s dělitelem objemu peněz
				# k obchodování navrátit volající třídě, aby ho mohla předat
				# obchodujícímu modulu a ten jej zpracoval pro nákup.
				else:
					adddict = {"sequencialbuy": int(amountheight)}
					b.update(adddict)
					self.localboughtscache.append(b)
		return buys

	def HandleSells(self, sells):
		"""
		V SynchronizeAlgorythms jsme už vyřešili případný konflikt mezi
		algorytmy. Teď můžeme pokud máme nějaké prodeje, prodávaný pár
		kompletně vymazat z lokální cache nákupů.
		:param sells:
		:return:
		"""
		pairs2sell = []
		if sells:
			for pairdict in sells:
				pairs2sell.append(pairdict["pair"])
		# unique
		pairs2sell = set(pairs2sell)
		# Odstraňujeme:
		for p in pairs2sell:
			for i in self.localboughtscache:
				if i["pair"] == p:
					self.localboughtscache.remove(i)

	def SequentialBuysManager(self, sells, buys):
		"""
		Řídí všechny funkce pro Sequential Buying a navrací
		aktualizovaný seznam se slovníky nákupů.
		:param sells:
		:param buys:
		:return:
		"""
		# Nejdříve odstraním konfliktní nákupy.
		# Modifikuju, proto i navracím, pouze nákupy.
		buys = self.SynchronizeAlgorythms(sells, buys)
		# Nyní budou jednotlivým nákupům přiřazena sekvenční čísla.
		buys = self.HandleSequentialNumbers(buys)
		# Nyní odstraním z místní cache všechny výskyty páru,
		# určeného k prodeji.
		self.HandleSells(sells)
		return buys





