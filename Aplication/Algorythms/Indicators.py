#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import talib
import numpy
import Helper


# ------------
# Třídy
# ------------

class TradingIndicators:
	"""
	Tato třída představuje implementaci indicatorů, používaných
	pro obchod.
	"""

	def __init__(self):
		self.config = Helper.Config()
		self.natrperiod = self.config.natrPeriod
		self.trimaultrafast = self.config.trimaUltraFast
		self.trimafast = self.config.trimaFast
		self.trimaslow = self.config.trimaSlow
		self.trimaultraslow = self.config.indicatorsLength
		self.rsiperiod = self.config.rsiPeriod
		self.macdslow = self.config.macdSlow
		self.macdfast = self.config.macdFast
		self.macdsignal = self.config.macdSignal
		self.momperiod = self.config.momPeriod
		self.stochastic_fast_k_period = self.config.stochastic_fast_k_period
		self.stochastic_slow_k_period = self.config.stochastic_slow_k_period
		self.stochastic_slow_d_period = self.config.stochastic_slow_d_period

	def natr(self, high, low, close, timeperiod=None):
		"""
		NATR = Normalized Average True Range (Volatility Indicators)
		Indikátor volatility. Obchodovatelná volatilita zdá se být
		nad 1.0 .
		:param high:
		:param low:
		:param close:
		:param timeperiod:
		:return float:
		"""
		if timeperiod is None:
			timeperiod = self.natrperiod
		# nejdříve vyřízneme potřebnou délku,
		# ke které přidáme jedno místo navíc,
		# protože výsledek je počítán z plné délky
		# 'timepepriod' a hodnotu navrací až v první
		# následující iteraci.
		high = high[-(timeperiod + 1):]
		low = low[-(timeperiod + 1):]
		close = close[-(timeperiod + 1):]
		# Převedeme na desetinná čísla s dvojitou přesností.
		high = [float(x) for x in high]
		low = [float(x) for x in low]
		close = [float(x) for x in close]
		# nyní ji převedeme na datové pole,
		# pro použití v talib.
		high = numpy.asarray(high)
		low = numpy.asarray(low)
		close = numpy.asarray(close)
		result = talib.NATR(high, low, close, timeperiod)
		# Vyřízneme poslední výsledek a
		# navracíme jako desetinné číslo.
		cutedresult = float(result[-1])
		# Vrátí desetinné číslo.
		return cutedresult

	def rsi(self, averages, timeperiod=None):
		"""
		RSI = Relative Strength Index (Momentum Indicators)
		:param averages:
		:param timeperiod:
		:return:
		"""
		if timeperiod is None:
			timeperiod = self.rsiperiod
		# nejdříve vyřízneme potřebnou délku,
		# ke které přidáme jedno místo navíc,
		# protože výsledek je počítán z plné délky
		# 'timepepriod' a hodnotu navrací až v první
		# následující iteraci.
		averages = averages[-(timeperiod + 1):]
		# Převedeme na desetinná čísla s dvojitou přesností.
		averages = [float(x) for x in averages]
		# převedeme na datové pole
		averages = numpy.asarray(averages)
		# Výsledek
		result = talib.RSI(averages, timeperiod)
		# Vyřízneme poslední výsledek a
		# navracíme jako desetinné číslo.
		cutedresult = float(result[-1])
		# Vrátí desetinné číslo.
		return cutedresult

	def stochastic(self, high, low, close, fastk_period=None, slowk_period=None, slowk_matype=0, slowd_period=None,
	               slowd_matype=0):
		"""
		Stochastic (Momentum Indicators)
		Inputs:
			prices: ['high', 'low', 'close']
		Parameters:
			fastk_period: 5
			slowk_period: 3
			slowk_matype: 0
			slowd_period: 3
			slowd_matype: 0
		Outputs:
			slowk
			slowd
		:param high:
		:param low:
		:param close:
		:param fastk_period:
		:param slowk_period:
		:param slowk_matype:
		:param slowd_period:
		:param slowd_matype:
		:return:
		"""
		if fastk_period is None:
			fastk_period = self.stochastic_fast_k_period
		if slowk_period is None:
			slowk_period = self.stochastic_slow_k_period
		if slowd_period is None:
			slowd_period = self.stochastic_slow_d_period
		# nejdříve vyřízneme potřebnou délku,
		# ke které přidáme jedno místo navíc,
		# protože výsledek je počítán z plné délky
		# 'timepepriod' a hodnotu navrací až v první
		# následující iteraci.
		edge = int(fastk_period + slowk_period + slowd_period)
		high = high[- edge:]
		low = low[- edge:]
		close = close[- edge:]
		# Převedeme na desetinná čísla s dvojitou přesností.
		high = [float(x) for x in high]
		low = [float(x) for x in low]
		close = [float(x) for x in close]
		# nyní ji převedeme na datové pole,
		# pro použití v talib.
		high = numpy.asarray(high)
		low = numpy.asarray(low)
		close = numpy.asarray(close)
		result = talib.STOCH(high, low, close, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)
		# Vyřízneme poslední výsledek a
		# navracíme jako desetinné číslo.
		overall = []
		for i in result:
			part = i.tolist()
			overall.append(part[-1])
		return tuple(overall)

	def macd(self, averages, fastperiod=None, slowperiod=None, signalperiod=None):
		"""
		Moving Average Convergence/Divergence (Momentum Indicators)
		Inputs:
		real: (any ndarray)
		Parameters:
		fastperiod: 12
		slowperiod: 26
		signalperiod: 9
		Outputs:
		macd
		macdsignal
		macdhist
		:param averages:
		:param fastperiod:
		:param slowperiod:
		:param signalperiod:
		:return:
		"""
		if slowperiod is None:
			slowperiod = self.macdslow
		if fastperiod is None:
			fastperiod = self.macdfast
		if signalperiod is None:
			signalperiod = self.macdsignal
		# nejdříve vyřízneme potřebnou délku,
		# ke které přidáme jedno místo navíc,
		# protože výsledek je počítán z plné délky
		# 'timepepriod' a hodnotu navrací až v první
		# následující iteraci.
		averages = averages[-(slowperiod + signalperiod + 1):]
		# Převedeme na desetinná čísla
		averages = [float(x) for x in averages]
		# převedeme na datové pole
		averages = numpy.asarray(averages)
		# Výsledek
		result = talib.MACD(averages, fastperiod, slowperiod, signalperiod)
		# Převedeme z datového pole na posloupnost.
		overall = []
		for i in result:
			part = i.tolist()
			overall.append(part[-1])
		# Navracíme entici tří hodnot: macd, macdsignal, macdhistogram.
		return tuple(overall)

	def trima(self, averages, ultrafastperiod=None, fastperiod=None, slowperiod=None):
		"""
		TRIMA = Triangular Moving Average (Overlap Studies)
		:param averages:
		:param ultrafastperiod:
		:param fastperiod:
		:param slowperiod:
		:return:
		"""
		if ultrafastperiod is None:
			ultrafastperiod = self.trimaultrafast
		if fastperiod is None:
			fastperiod = self.trimafast
		if slowperiod is None:
			slowperiod = self.trimaslow
		# nejdříve vyřízneme potřebnou délku.
		ultrafast = averages[-ultrafastperiod:]
		fast = averages[-fastperiod:]
		slow = averages[-slowperiod:]
		# Převedeme na desetinná čísla.
		ultrafast = [float(x) for x in ultrafast]
		fast = [float(x) for x in fast]
		slow = [float(x) for x in slow]
		# nyní ji převedeme na datové pole,
		# pro použití v talib.
		ultrafast = numpy.asarray(ultrafast)
		fast = numpy.asarray(fast)
		slow = numpy.asarray(slow)
		# Výsledky
		resultultrafast = talib.TRIMA(ultrafast, ultrafastperiod)
		resultfast = talib.TRIMA(fast, fastperiod)
		resultslow = talib.TRIMA(slow, slowperiod)
		# Z datového pole vyřízneme poslední výsledek
		# a navracíme jako desetinné číslo.
		cutultrafastresult = float(resultultrafast[-1])
		cutfastresult = float(resultfast[-1])
		cutslowresult = float(resultslow[-1])
		# Vrátí ntici desetinných čísel.
		return cutultrafastresult, cutfastresult, cutslowresult

	def indicatorsTrima(self, averages, period=None):
		# nejdříve vyřízneme potřebnou délku.
		averages = averages[-period:]
		# Převedeme na desetinná čísla.
		averages = [float(x) for x in averages]
		# nyní ji převedeme na datové pole,
		# pro použití v talib.
		averages = numpy.asarray(averages)
		# Výsledky
		result = talib.TRIMA(averages, period)
		# Z datového pole vyřízneme poslední výsledek
		# a navracíme jako desetinné číslo.
		cutresult = float(result[-1])
		# Vrátí ntici desetinných čísel.
		return cutresult

	def marketTrend(self, averages, ultraslowperiod=None):
		"""
		Vypočítává trend celého trhu, jako
		trimu ultra slow.
		:param averages:
		:param ultraslowperiod:
		:return:
		"""
		if ultraslowperiod is None:
			ultraslowperiod = self.trimaultraslow
		# nejdříve vyřízneme potřebnou délku.
		ultraslow = averages[-ultraslowperiod:]
		# Převedeme na desetinná čísla.
		ultraslow = [float(x) for x in ultraslow]
		# nyní ji převedeme na datové pole,
		# pro použití v talib.
		ultraslow = numpy.asarray(ultraslow)
		# Výsledky
		resultultraslow = talib.TRIMA(ultraslow, ultraslowperiod)
		# Z datového pole vyřízneme poslední výsledek
		# a navracíme jako desetinné číslo.
		cutresultultraslow = float(resultultraslow[-1])
		# Návrat
		return cutresultultraslow

	def ad(self, highs, lows, closes, volumes_currency):
		"""
		AD = Chaikin A/D Line (Volume Indicators)
		:param highs:
		:param lows:
		:param closes:
		:param volumes_currency:
		:return:
		"""
		# nejdříve vyřízneme potřebnou délku
		# a převedeme na desetinné číslo.
		high = float(highs[-1])
		low = float(lows[-1])
		close = float(closes[-1])
		volumes_currency = float(volumes_currency[-1])
		# převedeme na datová pole
		high = numpy.asarray((high,))
		low = numpy.asarray((low,))
		close = numpy.asarray((close,))
		volumes_currency = numpy.asarray((volumes_currency,))
		# Výsledek.
		result = talib.AD(high, low, close, volumes_currency)
		# Z datového pole vyřízneme poslední výsledek
		# a navracíme jako desetinné číslo.
		cutedresult = float(result[-1])
		# Vrátí desetinné číslo.
		return cutedresult

	def mom(self, averages, timeperiod=None):
		"""
		MMO = Momentum (Momentum Indicators)
		:param averages:
		:param timeperiod:
		:return:
		"""
		if timeperiod is None:
			timeperiod = self.momperiod
		# nejdříve vyřízneme potřebnou délku,
		# ke které přidáme jedno místo navíc,
		# protože výsledek je počítán z plné délky
		# 'timepepriod' a hodnotu navrací až v první
		# následující iteraci.
		averages = averages[-(timeperiod + 1):]
		# Převedeme na desetinná čísla
		averages = [float(x) for x in averages]
		# převedeme na datové pole
		averages = numpy.asarray(averages)
		# Výpočet
		result = talib.MOM(averages, timeperiod)
		cutedresult = float(result[-1])
		# Vrátí desetinné číslo.
		return cutedresult

	def bop(self, opens, highs, lows, closes):
		"""
		Balance Of Power (Momentum Indicators)
		Inputs:
			prices: ['open', 'high', 'low', 'close']
		Outputs:
			real
		:param open:
		:param high:
		:param low:
		:param close:
		:return:
		"""
		# nejdříve vyřízneme potřebnou délku
		# a převedeme na desetinné číslo.
		open = float(opens[-1])
		high = float(highs[-1])
		low = float(lows[-1])
		close = float(closes[-1])
		# převedeme na datová pole
		open = numpy.asarray((open,))
		high = numpy.asarray((high,))
		low = numpy.asarray((low,))
		close = numpy.asarray((close,))
		# Výsledek.
		result = talib.BOP(open, high, low, close)
		cutresult = float(result[0])
		return cutresult


############################################################
#
# Předpřipravené funkce pro možnou implementaci.
#
############################################################

def cmo(averages, timeperiod=14):
	"""
	CMO = Chande Momentum Oscillator (Momentum Indicators)
	:param averages:
	:param timeperiod:
	:return float:
	"""
	# nejdříve vyřízneme potřebnou délku,
	# ke které přidáme jedno místo navíc,
	# protože výsledek je počítán z plné délky
	# 'timepepriod' a hodnotu navrací až v první
	# následující iteraci.
	averages = averages[-(timeperiod + 1):]
	# převedeme na datové pole
	averages = numpy.asarray(averages)
	result = talib.CMO(averages, timeperiod)
	# Z datového pole vyřízneme poslední výsledek a navracíme jako desetinné číslo.
	cutedresult = float(result[-1])
	# Vrátí desetinné číslo.
	return cutedresult


def mom(averages, timeperiod=10):
	"""
	MMO = Momentum (Momentum Indicators)
	:param averages:
	:param timeperiod:
	:return:
	"""
	# nejdříve vyřízneme potřebnou délku,
	# ke které přidáme jedno místo navíc,
	# protože výsledek je počítán z plné délky
	# 'timepepriod' a hodnotu navrací až v první
	# následující iteraci.
	averages = averages[-(timeperiod + 1):]
	# převedeme na datové pole
	averages = numpy.asarray(averages)
	result = talib.MOM(averages, timeperiod)
	# Z datového pole vyřízneme poslední výsledek a navracíme jako desetinné číslo.
	cutedresult = float(result[-1])
	# Vrátí desetinné číslo.
	return cutedresult


def mfi(highs, lows, closes, volumes, timeperiod=None):
	"""
	Money Flow Index (Momentum Indicators)
	:param highs:
	:param lows:
	:param closes:
	:param volumes:
	:param timeperiod:
	:return:
	"""
	if timeperiod is None:
		timeperiod = 14
	# nejdříve vyřízneme potřebnou délku,
	# ke které přidáme jedno místo navíc,
	# protože výsledek je počítán z plné délky
	# 'timepepriod' a hodnotu navrací až v první
	# následující iteraci.
	highs = highs[-(timeperiod + 1):]
	lows = lows[-(timeperiod + 1):]
	closes = closes[-(timeperiod + 1):]
	volumes = volumes[-(timeperiod + 1):]
	# Převedeme na desetinná čísla
	highs = [float(x) for x in highs]
	lows = [float(x) for x in lows]
	closes = [float(x) for x in closes]
	volumes = [float(x) for x in volumes]
	# převedeme na datové pole
	highs = numpy.asarray(highs)
	lows = numpy.asarray(lows)
	closes = numpy.asarray(closes)
	volumes = numpy.asarray(volumes)
	# Výpočet
	result = talib.MFI(highs, lows, closes, volumes)
	# Převedeme z datového pole na posloupnost.
	overall = []
	for i in result:
		part = i.tolist()
		overall.append(part)
	# Vyřízneme poslední výsledek a
	# navracíme jako desetinné číslo.
	cutedresult = float(overall[-1])
	# Vrátí desetinné číslo.
	return cutedresult


def aroonosc(high, low, timeperiod=None):
	"""
	AROONOSC = Aroon Oscillator (Momentum Indicators)
	:param high:
	:param low:
	:param timeperiod:
	:return float:
	"""
	if timeperiod is None:
		timeperiod = 14
	# nejdříve vyřízneme potřebnou délku,
	# ke které přidáme jedno místo navíc,
	# protože výsledek je počítán z plné délky
	# 'timepepriod' a hodnotu navrací až v první
	# následující iteraci.
	high = high[-(timeperiod + 1):]
	low = low[-(timeperiod + 1):]
	# Převedeme na desetinná čísla s dvojitou přesností.
	high = [float(x) for x in high]
	low = [float(x) for x in low]
	# Převedeme na pole dat.
	high = numpy.asarray(high)
	low = numpy.asarray(low)
	# Výsledek
	result = talib.AROONOSC(high, low, timeperiod)
	# Převedeme z datového pole na posloupnost.
	overall = []
	for i in result:
		part = i.tolist()
		overall.append(part)
	# Z datového pole vyřízneme poslední výsledek
	# a navracíme jako desetinné číslo.
	cutedresult = float(overall[-1])
	# Vrátí desetinné číslo.
	return cutedresult


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


	# Přiřazení tříd.
	ti = TradingIndicators()

	# Data
	averages = [233.1153746875, 233.390525, 233.0800146875, 232.961025, 233.0500146875, 233.072093333333, 233.3100925,
	            233.0500534375, 233.050067142857, 233.0500803125, 233.050088666667, 233.100099642857, 233.0500834375,
	            233.050005, 233.050005, 233.050005, 233.343333, 233.150004333333, 233.43001, 233.550743333333,
	            233.542778928571, 234.292786666667, 234.168524666667, 233.631915333333, 233.277163, 233.25001,
	            233.573943461538, 233.687316, 233.711919285714, 233.741792666667, 233.7459775, 233.882070666667,
	            233.7554225, 233.795505, 233.519438, 233.450005, 233.728009333333, 233.583401, 233.550005,
	            233.746338333333, 233.1153746875, 233.390525, 233.0800146875, 232.961025, 233.0500146875,
	            233.072093333333, 233.3100925,
	            233.0500534375, 233.050067142857, 233.0500803125, 233.050088666667, 233.100099642857, 233.0500834375,
	            233.050005, 233.050005, 233.050005, 233.343333, 233.150004333333, 233.43001, 233.550743333333,
	            233.542778928571, 234.292786666667, 234.168524666667, 233.631915333333, 233.277163, 233.25001,
	            233.573943461538, 233.687316, 233.711919285714, 233.741792666667, 233.7459775, 233.882070666667,
	            233.7554225, 233.795505, 233.519438, 233.450005, 233.728009333333, 233.583401, 233.550005,
	            233.746338333333]
	lows = [232.20001, 232.21002, 232.21002, 232.20001, 232.30001, 232.3, 232.30007, 232.30009, 232.30013, 232.30015,
	        232.30001, 232.3002, 232.3, 232.30001, 232.30001, 232.30001, 232.30001, 232.4, 232.4, 232.40001, 232.40001,
	        232.42201, 232.883, 232.51001, 232.50002, 232.50002, 232.50002, 232.51005, 232.51023, 232.60001, 232.62601,
	        232.63001, 232.64007, 232.70201, 232.7, 232.70001, 232.70001, 232.71201, 232.80001, 232.80001]
	highs = [234.49999, 234.5, 234.49999, 233.8, 233.8, 234.46199, 234.46198, 233.8, 233.8, 233.8, 233.8, 234.49992,
	         233.8, 233.8, 233.8, 233.8, 234.5, 233.9, 234.49999, 234.49999, 234.49999, 234.75376, 234.75376,
	         234.75376,
	         234.75376, 234, 234.86451, 234.86451, 234.86451, 234.86451, 234.86451, 234.889, 234.889, 234.889, 234.889,
	         234.2, 234.889, 234.889, 234.3, 234.889]
	opens = [233.04973, 233.44973, 233.355005, 232.95502, 233.050005, 233.050025, 233.38102500000002, 233.050045,
	         233.05006500000002, 233.050075, 233.05009, 233.40006, 233.05011000000002, 233.050005, 233.050005,
	         233.050005, 233.050005, 233.15, 234.19999, 233.15001999999998, 233.60549500000002, 233.461005, 234.44383,
	         233.631885, 233.63196, 233.25001, 233.25001, 233.68728, 233.68737, 233.73226, 233.74526, 233.74729,
	         233.76453500000002, 233.795505, 233.795505, 233.45000499999998, 233.45000499999998, 233.800505,
	         233.550005,
	         233.550005]
	closes = [233.44973, 233.355005, 232.95502, 233.050005, 233.050025, 233.38103, 233.050045, 233.05006500000002,
	          233.050075, 233.05008500000002, 233.0501, 233.05011000000002, 233.050005, 233.050005, 233.050005,
	          233.050005, 233.15, 233.15000500000002, 233.15001999999998, 233.60549500000002, 233.461, 234.44383,
	          233.81838, 233.63196, 233.25001, 233.25001, 233.68727, 233.68736, 233.73226, 233.74526, 233.74728,
	          233.76451500000002, 233.451005, 233.795505, 233.45000499999998, 233.45000499999998, 233.800505,
	          233.550005, 233.550005, 233.844505]
	volumes = [31540.415189999985, 31560.067549374988, 31569.00043999999, 31569.00043999999, 31569.00043999999,
	           31569.00043999999, 31572.533994285714, 31574.49708, 31574.49708, 31574.49708, 31574.49708,
	           31578.069707142848, 31580.054499999984, 31580.054499999984, 31580.054499999984, 31580.054499999984,
	           31584.283166666675, 31586.397500000006, 31595.946626666675, 31600.721190000007, 31618.897917857135,
	           31658.855613333333, 31673.78537, 31678.387411999996, 31681.455439999994, 31681.455439999994,
	           31686.31544615384, 31695.003263333325, 31602.610322857137, 31555.55764000001, 31564.40266071429,
	           31584.82607999999, 31602.432152142857, 31611.914148000003, 31615.945200000006, 31615.945200000006,
	           31622.849413333326, 31626.301519999994, 31629.48894071428, 31634.69956333333]
	# funkce
	tr = ti.trima(averages)
	rs = ti.rsi(averages)
	a = ti.ad(highs, lows, closes, volumes)
	natr = ti.natr(highs, lows, closes)
	macd = ti.macd(averages)
	mom = ti.mom(averages)
	bop = ti.bop(opens, highs, lows, closes)

	# tisk
	clean()
	mezera()
	print("TRIMA:")
	print(tr)
	mezera()
	print("RSI:")
	print(rs)
	mezera()
	print("AD (volume indicator):")
	print(a)
	mezera()
	print("NATR:")
	print(natr)
	mezera()
	print("MACD:")
	print(macd)
	mezera()
	print("MOM:")
	print(mom)
	mezera()
	print("BOP:")
	print(bop)
	mezera()
