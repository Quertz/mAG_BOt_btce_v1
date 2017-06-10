#!/usr/bin/env python3
# Copyright (c) 2015-2016 janmagrot@gmail.com

import http.client
import urllib.request
import urllib.parse
import urllib.error
import json
import hashlib
import hmac
import time
import Logger
import Helper


# ------------
# Třídy
# ------------

class TradeApi:
    # TODO: implementovat key check.
    """
    Třída jež zajišťuje správné spojení a formátování pro Btc-e trade API.
    """

    def __init__(self):
        self.__logging = Logger.TapiLogging()
        self.__api = Helper.Config()
        self.__api_key = self.__api.apikey
        self.__api_secret = self.__api.secret

    # Soukromé metody ke kterým nemůžeme přistupovat.

    def __nonce(self):
        """
        Nastavení jedinečného čísla nonce,
        které je v našem případě, kvůli potřebě
        jeho neopakovatelnosti nastaveno na
        výši času v UTC, převedeného na integer
        a s přidanou hodnotou, aby nebylo možné
        ho snadno odvodit.
        Maximum pro nonce je: 4294967294
        Kvůli vyšší bezpečnosti přidávám k nonce,
        ještě 1448744535. Vycházím z předpokladu,
        že čím vyšší nonce tím méně možností k jejímu
        zfalčování.
        :return:
        """
        time.sleep(1)
        self.__nonce_v = str(int(time.time() + 1448744535))

    def __signature(self, params):
        """
        Podpis.
        :param params:
        :return:
        """
        sig = hmac.new(self.__api_secret, params.encode(), hashlib.sha512)
        return sig.hexdigest()

    def __api_call(self, method, params):
        """
        Api call soukromé metody, pro můj účet.
        Obsahuje paramatry 'param' a 'method'.
        :param method:
        :param params:
        :return:
        """
        self.__nonce()
        params['method'] = method
        params['nonce'] = str(self.__nonce_v)
        params = urllib.parse.urlencode(params)
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Key": self.__api_key,
            "Sign": self.__signature(params)
        }
        while True:
            try:
                conn = http.client.HTTPSConnection("btc-e.com", timeout=5)
                conn.request("POST", "/tapi", params, headers)
                response = conn.getresponse().read().decode()
                data = json.loads(response)
                conn.close()
                return data
            except http.client.HTTPException as e:
                self.__logging.logtapiconnectionerror(e)
                time.sleep(3)
                continue
            except Exception as e:
                self.__logging.logtapiconnectionerror(e)
                time.sleep(3)
                continue

            ###################################################################
            #
            # K metodám modulu lze přistupovat jen pomocí následujících metod,
            # neboť všechny předchozí metody, jsou metody soukromé.
            # Následující veřejné metody cyklíme, abychom měli jistotu,
            # že k požadavkům dojde a pokud ne nedojde, ani k následujícím
            # požadavkům.
            #
            ###################################################################

    # Veřejné metody ke kterým můžeme přistupovat.

    def getAccountInfo(self):
        counter = 1
        while True:
            info = self.__api_call('getInfo', {})
            if counter >= 5:
                if not info or info["success"] == 0:
                    self.__logging.logtapimethoderror("getAccountInfo", counter, info)
            if counter >= 35:
                return False
            if info:
                if info["success"] == 1:
                    return info
                elif info["success"] == 0:
                    error = str(info["error"])
                    if error.startswith("invalid api key"):
                        print("Vaše API klíče jsou chybné,"
                              "prosím vygenerujte si nové API klíče.")
                        break
                    elif error.startswith("invalid sign"):
                        print("Vaše API klíče jsou chybné,"
                              "prosím vygenerujte si nové API klíče.")
                        break
                    elif error.startswith("invalid nonce parameter"):
                        # Pokud je jen invalidní Nonce, nepotřebuju
                        # logovat, tudíž nepřičítám counter.
                        # time.sleep(), je již obsaženo v __nonce(), metodě.
                        continue
                    else:
                        # Tady to radši zacyklim, aby jsem alespoň viděl v logu,
                        # co se, případně stalo.
                        counter += 1
                        time.sleep(1)
                        continue
            else:
                counter += 1
                time.sleep(1)
                continue

    def activeOrders(self, tpair):
        counter = 1
        params = {"pair": tpair}
        while True:
            info = self.__api_call('ActiveOrders', params)
            if counter >= 5:
                if not info or info["success"] == 0:
                    self.__logging.logtapimethoderror("ActiveOrders", counter, info)
            if counter >= 35:
                return False
            if info:
                if info["success"] == 1:
                    return info
                elif info["success"] == 0:
                    error = str(info["error"])
                    if error.startswith("invalid api key"):
                        print("Vaše API klíče jsou chybné,"
                              "prosím vygenerujte si nové API klíče.")
                        break
                    elif error.startswith("invalid sign"):
                        print("Vaše API klíče jsou chybné,"
                              "prosím vygenerujte si nové API klíče.")
                        break
                    elif error.startswith("invalid nonce parameter"):
                        # Pokud je jen invalidní Nonce, nepotřebuju
                        # logovat, tudíž nepřičítám counter.
                        # time.sleep(), je již obsaženo v __nonce(), metodě.
                        continue
                    elif error == "no orders":
                        # Pokud budou návratové hodnoty "Done",
                        # je to pro mně pokyn, že všechny pokyny byly
                        # vyplněny.
                        return "Done"
                    else:
                        # Tady to radši zacyklim, aby jsem alespoň viděl v logu,
                        # co se, případně stalo.
                        counter += 1
                        time.sleep(1)
                        continue
            else:
                counter += 1
                time.sleep(1)
                continue

    def orderInfo(self, torderID):
        counter = 1
        params = {"order_id": torderID}
        while True:
            info = self.__api_call('OrderInfo', params)
            if counter >= 5:
                if not info or info["success"] == 0:
                    self.__logging.logtapimethoderror("OrderInfo", counter, info)
            if counter >= 35:
                return False
            if info:
                if info["success"] == 1:
                    return info
                elif info["success"] == 0:
                    error = str(info["error"])
                    if error.startswith("invalid api key"):
                        print("Vaše API klíče jsou chybné,"
                              "prosím vygenerujte si nové API klíče.")
                        break
                    elif error.startswith("invalid sign"):
                        print("Vaše API klíče jsou chybné,"
                              "prosím vygenerujte si nové API klíče.")
                        break
                    elif error.startswith("invalid nonce parameter"):
                        # Pokud je jen invalidní Nonce, nepotřebuju
                        # logovat, tudíž nepřičítám counter.
                        # time.sleep(), je již obsaženo v __nonce(), metodě.
                        continue
                    elif error == "invalid order":
                        # False je znamením neúspěchu.
                        return False
                    else:
                        # Tady to radši zacyklim, aby jsem alespoň viděl v logu,
                        # co se, případně stalo.
                        counter += 1
                        time.sleep(1)
                        continue
            else:
                counter += 1
                time.sleep(1)
                continue

    def trade(self, tpair, ttype, trate, tamount):
        counter = 1
        params = {
            "pair": tpair,
            "type": ttype,
            "rate": trate,
            "amount": tamount
        }
        while True:
            info = self.__api_call('Trade', params)
            if counter >= 5:
                if not info or info["success"] == 0:
                    self.__logging.logtapimethoderror("Trade", counter, info)
            if counter >= 35:
                return False
            if info:
                if info["success"] == 1:
                    return info
                elif info["success"] == 0:
                    error = str(info["error"])
                    if error.startswith("invalid api key"):
                        print("Vaše API klíče jsou chybné,"
                              "prosím vygenerujte si nové API klíče.")
                        break
                    elif error.startswith("invalid sign"):
                        print("Vaše API klíče jsou chybné,"
                              "prosím vygenerujte si nové API klíče.")
                        break
                    elif error.startswith("invalid nonce parameter"):
                        # Pokud je jen invalidní Nonce, nepotřebuju
                        # logovat, tudíž nepřičítám counter.
                        # time.sleep(), je již obsaženo v __nonce(), metodě.
                        continue
                    else:
                        # False je znamením neúspěchu.
                        return False
            else:
                counter += 1
                time.sleep(1)
                continue

    def CancelOrder(self, torder_id):
        counter = 1
        params = {"order_id": torder_id}
        while True:
            info = self.__api_call('CancelOrder', params)
            if counter >= 5:
                if not info or info["success"] == 0:
                    self.__logging.logtapimethoderror("CancelOrder", counter, info)
            if counter >= 35:
                return False
            if info:
                if info["success"] == 1:
                    return info
                elif info["success"] == 0:
                    error = str(info["error"])
                    if error == "invalid api key":
                        print("Vaše API klíče jsou chybné,"
                              "prosím vygenerujte si nové API klíče.")
                        break
                    elif error == "invalid sign":
                        print("Vaše API klíče jsou chybné,"
                              "prosím vygenerujte si nové API klíče.")
                        break
                    elif error.startswith("invalid nonce parameter"):
                        # Pokud je jen invalidní Nonce, nepotřebuju
                        # logovat, tudíž nepřičítám counter.
                        # time.sleep(), je již obsaženo v __nonce(), metodě.
                        continue
                    elif error.startswith("bad status"):
                        # Pokud budou návratové hodnoty "Done",
                        # je to pro mně pokyn, že všechny pokyny byly
                        # vyplněny.
                        return "Done"
                    else:
                        # Tady to radši zacyklim, aby jsem alespoň viděl v logu,
                        # co se, případně stalo.
                        counter += 1
                        time.sleep(1)
                        continue
            else:
                counter += 1
                time.sleep(1)
                continue


# ------------
# Testy:
# ------------

if __name__ == "__main__":

    def mezera():
        print("-" * 240)


    def clean():
        print("\n" * 70)


    clean()

    tra = TradeApi()
    accinfo = tra.getAccountInfo()
    ao = tra.activeOrders("btc_usd")
    oi = tra.orderInfo(15411222)
    co = tra.CancelOrder(15411222)

    mezera()
    print("Informace o účtu: \n")
    print(accinfo, "\n")
    print("Aktivní příkazy pro btc_usd \n")
    print(ao)
    print("Order informace pro fejkový order_ID: \n")
    print(oi)
    print("Cancel order pro fejkový order ID: \n")
    print(co)
