#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import Helper


"""
Tento modul obsahuje pouze třídy, jež ze zadané posloupnosti dat
vyhodnocují, zda je pár vhodný k nákupu a metodu jejich
vyhodnocování. Zadaným argumentem je posloupnost s daty o jednom
měnovém páru. Návratovou hodnotou je slovník s dvojicemi dat, názvem
páru, pak názvem oscilátoru jako klíčem a booleanovskou hodnotou
jako hodnotou.
"""


# ------------
# Třídy
# ------------


class Methods4BuyAlgorythms:
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

	# Obdrží pár z datasetu:

	def GetPair(self, dataset):
		"""
		Vyzíská název páru.
		:param dataset:
		:return str:
		"""
		pair = None
		for key, value in dataset.items():
			if key == "pair":
				pair = value
		return pair

	def GetPrice(self, dataset):
		price = None
		for key, value in dataset.items():
			if key == "avg_price":
				prices = reversed(value)
				prices = list(prices)
				# Poslední hodnota nejaktuálnější.
				price = float(prices[0])
		return price

	# Výpočet volatility:

	def NatrEma(self, dataset):
		"""
		Výpočet volatility pomocí NAtrema a Natr.
		:param dataset:
		:return:
		"""
		natremadata = []
		simplenatrdata = []
		for key, value in dataset.items():
			if key == "natrema":
				natremadata = list(value)
		for key, value in dataset.items():
			if key == "natr":
				simplenatrdata = list(value)
		# Reversujeme abychom mohli dobře stříhat.
		reversednatremadata = list(reversed(natremadata))
		rev = list(reversed(simplenatrdata))
		cut = rev[:int(self.config.volatilityoffset - 1)]
		res = float(sum(cut) / len(cut))
		# Inicializace proměnných pro jednotlivé pokyny.
		pbuy = None
		nbuy = None
		buy = None
		# Porovnání natremy.
		if reversednatremadata[0] > self.config.minvolatility:
			pbuy = True
		else:
			pbuy = False
		# Porovnání natr.
		if res > self.config.minvolatility:
			nbuy = True
		else:
			nbuy = False
		# Porovnání natr a natremy.
		if nbuy and pbuy:
			buy = True
		else:
			buy = False
		# návrat.
		return buy

	def VolatileNatrEma(self, dataset):
		"""
		Výpočet volatility pomocí NAtrema a Natr.
		:param dataset:
		:return:
		"""
		natremadata = []
		simplenatrdata = []
		for key, value in dataset.items():
			if key == "natrema":
				natremadata = list(value)
		for key, value in dataset.items():
			if key == "natr":
				simplenatrdata = list(value)
		# Reversujeme abychom mohli dobře stříhat.
		reversednatremadata = list(reversed(natremadata))
		rev = list(reversed(simplenatrdata))
		cut = rev[:int(self.config.volatilityoffset - 1)]
		res = float(sum(cut) / len(cut))
		# Inicializace proměnných pro jednotlivé pokyny.
		pbuy = None
		nbuy = None
		buy = None
		# Porovnání natremy.
		if reversednatremadata[0] > self.config.minvolatility:
			pbuy = True
		else:
			pbuy = False
		# Porovnání natr.
		if res > 0.8:
			nbuy = True
		else:
			nbuy = False
		# Porovnání natr a natremy.
		if nbuy and pbuy:
			buy = True
		else:
			buy = False
		# návrat.
		return buy

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
					datatrimaslow = list(reversed(value))
			return datatrimaslow

		datatrimaslow = getData()
		if datatrimaslow[0] > datatrimaslow[1] > datatrimaslow[2]:
			buy = True
		else:
			buy = False
		return buy

	# Trima:

	def FullyGrowingTrima(self, dataset):
		"""
		Nejpřísnější výpočet pro stav a vztah,
		trimafast a trimaslow.
		:param dataset:
		:return:
		"""
		datatrimafast = []
		datatrimaultrafast = []
		datatrimaslow = []
		datatrimaultraslow = []
		for key, value in dataset.items():
			if key == "trimaultrafast":
				datatrimaultrafast = list(reversed(value))
		for key, value in dataset.items():
			if key == "trimafast":
				datatrimafast = list(reversed(value))
		for key, value in dataset.items():
			if key == "trimaslow":
				datatrimaslow = list(reversed(value))
		for key, value in dataset.items():
			if key == "trimaultraslow":
				datatrimaultraslow = list(reversed(value))
		if datatrimaultrafast[0] > datatrimafast[0] > datatrimaslow[0] > datatrimaultraslow[0]:
			buy = True
		else:
			buy = False
		return buy

	def GrowingFastEmas(self, dataset):
		"""
		Nejpřísnější výpočet pro stav a vztah,
		trimafast a trimaslow.
		:param dataset:
		:return:
		"""
		datatrimafast = []
		datatrimaultrafast = []
		for key, value in dataset.items():
			if key == "trimaultrafast":
				datatrimaultrafast = list(reversed(value))
		for key, value in dataset.items():
			if key == "trimafast":
				datatrimafast = list(reversed(value))
		if datatrimaultrafast[0] > datatrimaultrafast[1] and datatrimafast[0] < datatrimaultrafast[
			0]:
			buy = True
		else:
			buy = False
		return buy

	# Volumes

	def GrowingVolumes(self, dataset):
		"""
		Nejpřísnější výpočet pro stav a vztah,
		trimafast a trimaslow.
		:param dataset:
		:return:
		"""
		volumes = []
		for key, value in dataset.items():
			if key == "volumes":
				volumes = list(reversed(value))
		if volumes[0] > volumes[1] > volumes[2]:
			buy = True
		else:
			buy = False
		return buy

	# RSI:

	def SimpleRsi(self, dataset):
		"""
		Zpracování macd signálů.
		:param dataset:
		:return:
		"""
		rsidata = []
		for key, value in dataset.items():
			if key == "rsi":
				rsidata = list(value)
		rsidata = list(reversed(rsidata))
		if rsidata[1] < self.config.rsiBotom < rsidata[0]:
			buy = True
		else:
			buy = False
		return buy

	def RsiEma(self, dataset):
		"""
		Zpracování macd signálů.
		:param dataset:
		:return:
		"""
		rsiemadata = []
		for key, value in dataset.items():
			if key == "rsiema":
				rsiemadata = list(value)
		rsiemadata = list(reversed(rsiemadata))
		if rsiemadata[0] > rsiemadata[1] > rsiemadata[2]:
			buy = True
		else:
			buy = False
		return buy

	# Sochastic:

	def StochasticEma(self, dataset):
		"""
		Plné zpracování stochastiku.
		:param dataset:
		:return:
		"""
		stoch_k_data = []
		for key, value in dataset.items():
			if key == "stochema":
				stoch_k_data = list(value)
		stoch_k_data = list(reversed(stoch_k_data))
		buy = False
		if stoch_k_data[0] > stoch_k_data[1] > stoch_k_data[2]:
			buy = True
		return buy

	# Macd:

	def MacdEma(self, dataset):
		"""
		Zpracování macd signálů.
		:param dataset:
		:return:
		"""
		macdemadata = []
		for key, value in dataset.items():
			if key == "macdema":
				macdemadata = list(value)
		macdemadata = list(reversed(macdemadata))
		if macdemadata[0] > macdemadata[1] > macdemadata[2]:
			buy = True
		else:
			buy = False
		return buy

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
		buy = True
		for key, value in dataset.items():
			if key == "adema":
				ademadata = list(value)
		ademadata = list(reversed(ademadata))
		ademadata = ademadata[:3]
		for i in ademadata:
			if i < 50.0:
				buy = False
		return buy

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
		buy = True
		nbuy = False
		abuy = None
		for key, value in dataset.items():
			if key == "adema":
				ademadata = list(reversed(value))
		for key, value in dataset.items():
			if key == "ad":
				addata = list(reversed(value))
		addata = addata[:2]
		if ademadata[0] > ademadata[1] > ademadata[2] and ademadata[0] > 0.0 and ademadata[1] > 0.0:
			nbuy = True
		for i in addata:
			if i < 0.0:
				buy = False
		if buy and nbuy:
			abuy = True
		else:
			abuy = False
		return abuy

	# Mom:

	def MomEma(self, dataset):
		"""
		Přísný výpočet pro mom.
		:param dataset:
		:return:
		"""
		momemadata = []
		for key, value in dataset.items():
			if key == "momema":
				momemadata = list(value)
		momemadata = list(reversed(momemadata))
		if momemadata[0] > momemadata[1] > momemadata[2] > momemadata[3]:
			buy = True
		else:
			buy = False
		return buy

	# Bop:

	def BopEma(self, dataset):
		"""
		Přísný výpočet pro mom.
		:param dataset:
		:return:
		"""
		bopemadata = []
		for key, value in dataset.items():
			if key == "bopema":
				bopemadata = list(value)
		bopemadata = list(reversed(bopemadata))
		if bopemadata[0] > bopemadata[1] > bopemadata[2]:
			buy = True
		else:
			buy = False
		return buy


class BuyAlgorythms:
	"""
	Tato třídy obsahuje algorytmy, pro vyhodnocování
	posloupností dat.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.buymethods = Methods4BuyAlgorythms()
		self.dataset = None

	# První Algorytmus:
	def FirstAlgorythm(self, dataset):
		"""
		Tato metoda provede vyhodnocení,
		pro nákup.
		:param dataset:
		:return:
		"""

		self.dataset = dataset

		pairdict = {}
		pairdict["pair"] = self.buymethods.GetPair(self.dataset)
		pairdict["price"] = self.buymethods.GetPrice(self.dataset)
		pairdict["natr"] = self.buymethods.NatrEma(self.dataset)
		pairdict["rsiema"] = self.buymethods.RsiEma(self.dataset)
		pairdict["adema"] = self.buymethods.AdEma(self.dataset)
		pairdict["volumes"] = self.buymethods.GrowingVolumes(self.dataset)
		# Nový
		pairdict["trima"] = self.buymethods.GrowingFastEmas(self.dataset)
		return pairdict

	# Druhý Algorytmus:
	def SecondAlgorythm(self, dataset):
		"""
		Tato metoda provede vyhodnocení,
		pro nákup.
		:param dataset:
		:return:
		"""

		self.dataset = dataset

		pairdict = {}
		pairdict["pair"] = self.buymethods.GetPair(self.dataset)
		pairdict["price"] = self.buymethods.GetPrice(self.dataset)
		pairdict["market"] = self.buymethods.MarketTrend(self.dataset)
		pairdict["volume"] = self.buymethods.GrowingVolumes(self.dataset)
		pairdict["ad"] = self.buymethods.VolatileAdEma(self.dataset)
		pairdict["macd"] = True
		return pairdict
