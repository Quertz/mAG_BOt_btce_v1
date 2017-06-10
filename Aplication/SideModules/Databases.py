#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import sqlite3
import os
import sys

# Přidání dočasných cest do $PYTHONPATH
# Seznam složek generujeme v reálném čase, bez složky s databázemi.
directories = [d for d in os.listdir(os.getcwd()) if os.path.isdir(d) and d != "0_databases" and d != "0_temporary"]
# Výchozí složka
rootdir = os.getcwd()
# Přidání všech podsložek.
for i in directories:
        os.chdir(i)
        d = os.getcwd()
        sys.path.insert(0, d)
        os.chdir(rootdir)

import Api
import Helper


# ------------
# Konstanty
# ------------

PAIRSDATABASE = "./0_databases/pairsinfo.db"
CANDLESDATABASE = "./0_databases/candles.db"
INDICATORSDATABASE = "./0_databases/indicators.db"
SIGNALSDATABASE = "./0_databases/signals.db"
TICKERSDATABASE = "./0_databases/tickers.db"


# ------------
# Třídy
# ------------


class CreateTables:
        """
        Tato třída vytvoří databáze a označí modul za aktivovaný.
        """

        def __init__(self):
                """
                Zde inicializuji výpovědi o tom zda a jaké jsou databáze již
                vytvořeny.
                """
                self.allTablesCreated = False
                self.config = Helper.Config()

        def buildPairsTable(self):
                """
                Tato metoda vytvoří, či aktualizuje databázi měnových párů.
                :return:
                """
                if not self.allTablesCreated:
                        con = sqlite3.connect(PAIRSDATABASE)
                        cur = con.cursor()

                        def getPairsFullInfo():
                                """
                                Získá aktuální obchodovatelné páry z btc-e.com pomocí modulu api.py
                                a porovná je s páry, které chceme obchodovat v nastavení.
                                Pokud je pár v obou skupinách, vytvoří pro něj řádek v databázi.
                                """
                                get = Api.PublicApi()
                                raw = dict(get.getPublicInfo())
                                rawpairsinfo = raw["pairs"]
                                tradingpairs = self.config.tradingPairs
                                pairsinfolist = []
                                while True:
                                        for key, value in rawpairsinfo.items():
                                                if key in tradingpairs:
                                                        pairdict = {
                                                                "pair": key,
                                                                "decimal": value["decimal_places"],
                                                                "min_price": value["min_price"],
                                                                "max_price": value["max_price"],
                                                                "fee": value["fee"],
                                                                "min_amount": value["min_amount"]
                                                        }
                                                        pairsinfolist.append(pairdict)
                                                        continue
                                        return pairsinfolist

                        cur.execute("CREATE TABLE IF NOT EXISTS pairs(pair,decimal,min_price,max_price,fee,min_amount )")
                        con.commit()
                        # Aktualizuj
                        cur.execute("DELETE FROM pairs")
                        for d in getPairsFullInfo():
                                cur.execute("INSERT OR IGNORE INTO pairs VALUES(?,?,?,?,?,?)",
                                            (d["pair"], d["decimal"], d["min_price"], d["max_price"], d["fee"],
                                             d["min_amount"],))
                        con.commit()
                        con.close()
                else:
                        pass

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

        def buildCandlesticksTable(self):
                """
                Tato metoda postaví table databáze candlesticků.
                Zde využíváme formát čase v server_time_localtime pro
                snadné řízení cyklů minut a pro čitelnost.
                :return:
                """
                if not self.allTablesCreated:
                        con = sqlite3.connect(CANDLESDATABASE)
                        cur = con.cursor()
                        for pair in self.pairsFromDatabase():
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
                                        ")".format(p="candlesticks_" + pair, ))
                        con.commit()
                        con.close()
                else:
                        pass

        def buildIndicatorsTable(self):
                """
                Postaví databází pro oscilátory.
                """
                if not self.allTablesCreated:
                        con = sqlite3.connect(INDICATORSDATABASE)
                        cur = con.cursor()
                        for pair in self.pairsFromDatabase():
                                cur.execute(
                                        "CREATE TABLE IF NOT EXISTS {p}("
                                        "avg_price,"
                                        "NATR,"
                                        "RSI,"
                                        "STOCH_K,"
                                        "STOCH_D,"
                                        "MACD,"
                                        "MACDsign,"
                                        "MACDhist,"
                                        "TRIMAultrafast,"
                                        "TRIMAfast,"
                                        "TRIMAslow,"
                                        "AD,"
                                        "BOP,"
                                        "MOM"
                                        ")".format(p="signals_" + pair, ))
                                con.commit()
                else:
                        pass

        def buildSignalsTable(self):
                """
                Tato funkce postaví databázi pro nová data
                oscilátorů.
                :return:
                """
                con = sqlite3.connect(SIGNALSDATABASE)
                cur = con.cursor()
                for pair in self.pairsFromDatabase():
                        cur.execute(
                                "CREATE TABLE IF NOT EXISTS {p}("
                                "RSIema,"
                                "MACDema,"
                                "STOCHema,"
                                "TRIMAultraslow,"
                                "ADema,"
                                "BOPema,"
                                "NATRema,"
                                "MOMema"
                                ")".format(p="signals_" + pair, ))
                con.commit()
                con.close()

        def buildTickersTable(self):
                """
                Tato funkce postaví databázi pro nová data
                oscilátorů.
                :return:
                """
                con = sqlite3.connect(TICKERSDATABASE)
                cur = con.cursor()
                for pair in self.pairsFromDatabase():
                        cur.execute(
                                "CREATE TABLE IF NOT EXISTS {p}("
                                "high,"
                                "low,"
                                "sell,"
                                "buy,"
                                "avg,"
                                "last,"
                                "vol,"
                                "vol_cur"
                                ")".format(p="tickers_" + pair, ))
                con.commit()
                con.close()

        def cleanCurrentTables(self):
                """
                Vyčistí stoly signálů a candlesticků.
                """
                for pair in self.pairsFromDatabase():
                        con = sqlite3.connect(CANDLESDATABASE)
                        cur = con.cursor()
                        cur.execute("DELETE FROM candlesticks_" + str(pair))
                        con.commit()
                        con.close()
                for pair in self.pairsFromDatabase():
                        con = sqlite3.connect(SIGNALSDATABASE)
                        cur = con.cursor()
                        cur.execute("DELETE FROM signals_" + str(pair))
                        con.commit()
                        con.close()
                for pair in self.pairsFromDatabase():
                        con = sqlite3.connect(TICKERSDATABASE)
                        cur = con.cursor()
                        cur.execute("DELETE FROM tickers_" + str(pair))
                        con.commit()
                        con.close()
                return True

        def buildAll(self):
                """
                Tato metoda vyvolá ostatní metody pro
                stavbu databází.
                """
                if not self.allTablesCreated:
                        self.buildPairsTable()
                        self.buildCandlesticksTable()
                        self.buildIndicatorsTable()
                        self.buildSignalsTable()
                        self.buildTickersTable()
                        self.allTablesCreated = True
                return self.allTablesCreated


def main():
        """
        Vyvolá celý modul.
        :return:
        """
        # Volání
        # Instance
        ct = CreateTables()
        # Proměnné funkcí
        ct.buildAll()
        ct.cleanCurrentTables()


main()
