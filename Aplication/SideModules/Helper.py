#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com


import logging
from configparser import ConfigParser


class Config:
    """
    Načte konfigurační soubor od uživatele a uchová zadané
    hodnoty v proměnných aplikace.
    """

    def __init__(self, keys="../settings/keys.ini", settings="../settings/settings.ini", emails="../settings/emails.ini"):
        self.keysfile = keys
        self.emailsfile = emails
        self.settingsfile = settings
        self.parser = ConfigParser()
        # Páry pro obchodování:
        self.tradingPairs = None
        # API
        self.api1 = None
        self.apikey = None
        # Převádíme na str(), protože api.py to vyžduje.
        self.api2 = None
        self.secret = None
        self.sendMails = None
        self.sender = None
        self.sendersPassword = None
        self.recepient = None
        # Nastavení Settings.
        self.datacollecting = None
        self.simMode = None
        self.usePricePolicy = None
        self.useLosingsPolicy = None
        self.losingsPolicyOffset = None
        self.pricePolicyRoofOffset = None
        self.pricePolicyBottomOffset = None
        self.sequencialbuying = None
        self.bigtickerfreq = None
        self.candlestickLenght = None
        self.missingCandlesLength = None
        self.overalldatalenght = None
        self.indicatorsLength = None
        self.usefirstalgorythm = None
        self.usesecondalgorythm = None
        # Trading
        self.buySlipage = None
        self.sellSlipage = None
        # Signals
        self.minvolatility = None
        self.natrPeriod = None
        self.natrEmaSlow = None
        self.volatilityoffset = None
        self.trimaUltraFast = None
        self.trimaFast = None
        self.trimaSlow = None
        self.rsiPeriod = None
        self.rsiEmaSlow = None
        self.rsiBotom = None
        self.rsiRoof = None
        self.stochasticBottom = None
        self.stochasticRoof = None
        self.stochastic_fast_k_period = None
        self.stochastic_slow_k_period = None
        self.stochastic_slow_d_period = None
        self.stochasticEmaSlow = None
        self.macdSlow = None
        self.macdFast = None
        self.macdSignal = None
        self.macdEmaSlow = None
        self.adPeriod = None
        self.adEmaSlow = None
        self.momPeriod = None
        self.momEmaSlow = None
        self.bopEmaSlow = None
        # Backtesting
        self.initialDolars = None

        # Aktualizujeme a nahrajeme nastavení:
        self.updateALL()
        self.parser.read(self.keysfile, encoding="UTF-8")

    def getTradingPairs(self):
        """
        Vyzíská ze složky s nastavením páry se kterými
        má obchodovat.
        :return:
        """
        file = "../settings/pairs"
        allpairs = []
        fout = open(file, "r", encoding="UTF-8")
        for i in fout:
            i = str(i)
            allpairs.append(i.rstrip('\n'))
        return allpairs

    def updateALL(self):
        """
        Aktualizuj a uchovej všechna uživatelská nastavení.
        :return:
        """
        # TODO: Pokud nenajde soubor vyvolá vyjímku.
        self.parser.read(self.keysfile, encoding="UTF-8")
        # API
        self.api1 = self.parser.get("API", "key")
        self.apikey = bytes(self.api1, encoding="UTF-8")
        # Převádíme na str(), protože api.py to vyžduje.
        self.api2 = self.parser.get("API", "secret")
        self.secret = bytes(self.api2, encoding="UTF-8")

        # TODO: Pokud nenajde soubor vyvolá vyjímku.
        self.parser.read(self.emailsfile, encoding="UTF-8")
        self.sendMails = self.parser.getboolean("Mails", "sendMails")
        self.sender = str(self.parser.get("Mails", "sender"))
        self.sendersPassword = str(self.parser.get("Mails", "mailPassword"))
        self.recepient = str(self.parser.get("Mails", "recepient"))

        # TODO: Pokud nenajde soubor vyvolá vyjímku.
        self.parser.read(self.settingsfile, encoding="UTF-8")
        # Nastavení Settings.
        self.datacollecting = self.parser.getboolean("Settings", "dataCollecting")
        self.simMode = self.parser.getboolean("Settings", "simMode")
        self.usePricePolicy = self.parser.getboolean("Settings", "usePricePolicy")
        self.pricePolicyRoofOffset = self.parser.getfloat("Settings", "pricePolicyRoofOffset")
        self.pricePolicyBottomOffset = self.parser.getfloat("Settings", "pricePolicyBottomOffset")
        self.useLosingsPolicy = self.parser.getboolean("Settings", "useLosingsPolicy")
        self.losingsPolicyOffset = self.parser.getfloat("Settings", "losingsPolicyOffset")
        self.sequencialbuying = self.parser.getint("Settings", "sequencialBuying")
        self.bigtickerfreq = self.parser.getint("Settings", "bigtickerfreq")
        self.candlestickLenght = self.parser.getint("Settings", "candlestickLenght")
        self.missingCandlesLength = self.parser.getint("Settings", "missingCandlesLength")
        self.overalldatalenght = self.parser.getint("Settings", "overalldatalenght")
        self.indicatorsLength = self.parser.getint("Settings", "indicatorsLength")
        self.usefirstalgorythm = self.parser.getboolean("Settings", "useFirstAlgorythm")
        self.usesecondalgorythm = self.parser.getboolean("Settings", "useSecondAlgorythm")

        # Trading
        self.tradingPairs = self.getTradingPairs()
        self.buySlipage = self.parser.getfloat("Trading", "buySlipage")
        self.sellSlipage = self.parser.getfloat("Trading", "sellSlipage")

        # Signals
        self.minvolatility = self.parser.getfloat("Signals", "min_volatility")
        self.natrPeriod = self.parser.getint("Signals", "natrPeriod")
        self.natrEmaSlow = self.parser.getint("Signals", "natrEmaSlow")
        self.volatilityoffset = self.parser.getint("Signals", "volatility_offset")
        self.trimaUltraFast = self.parser.getint("Signals", "trimaUltraFast")
        self.trimaFast = self.parser.getint("Signals", "trimaFast")
        self.trimaSlow = self.parser.getint("Signals", "trimaSlow")
        self.rsiPeriod = self.parser.getint("Signals", "rsiPeriod")
        self.rsiEmaSlow = self.parser.getint("Signals", "rsiEmaSlow")
        self.rsiBotom = self.parser.getfloat("Signals", "rsiBotom")
        self.rsiRoof = self.parser.getfloat("Signals", "rsiRoof")
        self.stochasticBottom = self.parser.getfloat("Signals", "stochasticBottom")
        self.stochasticRoof = self.parser.getfloat("Signals", "stochasticRoof")
        self.stochasticEmaSlow = self.parser.getint("Signals", "stochasticEmaSlow")
        self.stochastic_fast_k_period = self.parser.getint("Signals", "stochastic_fast_k_period")
        self.stochastic_slow_k_period = self.parser.getint("Signals", "stochastic_slow_k_period")
        self.stochastic_slow_d_period = self.parser.getint("Signals", "stochastic_slow_d_period")
        self.macdSlow = self.parser.getint("Signals", "macdSlowPeriod")
        self.macdFast = self.parser.getint("Signals", "macdFastPeriod")
        self.macdSignal = self.parser.getint("Signals", "macdSignalPeriod")
        self.macdEmaSlow = self.parser.getint("Signals", "macdEmaSlow")
        self.adPeriod = self.parser.getint("Signals", "adPeriod")
        self.adEmaSlow = self.parser.getint("Signals", "adEmaSlow")
        self.momPeriod = self.parser.getint("Signals", "momPeriod")
        self.momEmaSlow = self.parser.getint("Signals", "momEmaSlow")
        self.bopEmaSlow = self.parser.getint("Signals", "bopEmaSlow")

        # Backtesting
        self.initialDolars = self.parser.getfloat("Backtesting", "initialDolars")


if __name__ == "__main__":
    # Funkce
    def mezera():
        print("#" * 70)


    def clean():
        print("\n" * 50)


    # Testy pro třídu Config()
    con = Config()

    # Tisk
    print("Vytiskne vystup z třídy Config: \n")
    if con.apikey:
        print(con.apikey)
    if con.secret:
        print(con.secret)
    print(con.simMode)
    print(con.tradingPairs)
    print(con.sendMails)
    print(con.sender)
    print(con.sendersPassword)
    print(con.recepient)
    print("PricePolicyRoof a Bottom:" + str(con.pricePolicyRoofOffset + " " + con.pricePolicyBottomOffset))
