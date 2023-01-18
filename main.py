import requests
import json
import threading
import datetime
import os
import talib
import math

import pandas as pd
import numpy as np


from otwieranie import Kupowanie, Sprzedawanie
from zamykanie import ZamknijPoz

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
ACCOUNT_ID = os.environ.get('ACCOUNT_ID')

# globalne zmienne do sprawdzania czy jest otwarta pozycja
global kupione
global sprzedane
global oczekiwanieNaPrzeciecie
global bodyBuy
global bodySell
global bodyCloseLong
global bodyCloseShort
global paraWalutowa
paraWalutowa = "EUR_USD"
kupione = False
sprzedane = False
oczekiwanieNaPrzeciecie = False

# body do kupowania waluty
bodyCloseLong = '{"longUnits": "ALL"}'
bodyCloseShort = '{"shortUnits": "ALL"}'


headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {ACCESS_TOKEN}',
}


# funkcja sprawdza czy istnieje otwarta pozycja zwraca True lub False
def sprawdzOtwartePoz():
    res = requests.get(f"https://api-fxpractice.oanda.com/v3/accounts/{ACCOUNT_ID}/openPositions", headers=headers)

    pozycje = res.json()
    # print(pozycje)
    pozycje = pozycje['positions']
    if (len(pozycje) == 0):
        # print("Nie ma otwartych pozycji")
        return False

    for poz in pozycje:
        if (poz['instrument'] == paraWalutowa):
            print("Jest otwarta pozycja")
            return True
        else:
            print("Nie ma otwartych pozycji")
            return False

def transakcja(przedPrzedOstatnia, przedOstatnia, ostatnia, movingAV):


    bodyCloseLongText = json.loads(bodyCloseLong)
    bodyCloseLongText = json.dumps(bodyCloseLongText)

    bodyCloseShortText = json.loads(bodyCloseShort)
    bodyCloseShortText = json.dumps(bodyCloseShortText)

    czyOtwarda = sprawdzOtwartePoz()

    return

def sredniaWazona(swieczki, dlugosc):
    sumaSwieczek = 0
    sumaDlugosci = 0
    dlugoscKopia = dlugosc

    for i in range(int(dlugosc), 0, -1):
        sumaDlugosci = sumaDlugosci + i

    if (isinstance(swieczki, list)):
    # swieczki musza byc w kolejności od najwcześniejszej do najpozniejszej
        swieczki.reverse()
        for swieczka in swieczki:
            sumaSwieczek = sumaSwieczek + (float(swieczka) * dlugoscKopia)
            dlugoscKopia = dlugoscKopia - 1
        return round((sumaSwieczek / sumaDlugosci), 5)
    else:
        return round((swieczki / sumaDlugosci), 5)

def weighted_moving_average(series, lookback = None) -> float:
    if not lookback:
        lookback = len(series)
    if len(series) == 0:
        return 0
    assert 0 < lookback <= len(series)

    wma = 0
    lookback_offset = len(series) - lookback
    for index in range(lookback + lookback_offset - 1, lookback_offset - 1, -1):
        weight = index - lookback_offset + 1
        wma += series[index] * weight
    return wma / ((lookback ** 2 + lookback) / 2)


def hull_moving_average(series, lookback) -> float:
    assert lookback > 0
    hma_series = []
    for k in range(int(lookback ** 0.5), -1, -1):
        s = series[:-k or None]
        wma_half = weighted_moving_average(s, min(lookback // 2, len(s)))
        wma_full = weighted_moving_average(s, min(lookback, len(s)))
        hma_series.append(wma_half * 2 - wma_full)
    return weighted_moving_average(hma_series)


def hekinBreakout():
    # odpala funkcje w nowym watku. Funkcja sie nie chainuje wiec nie będzie błędów. Wykonuje się co 2 sekundy
    threading.Timer(2.0, hekinBreakout).start()

    global paraWalutowa

    timeFrame = "M5"
    zamknieciaSwieczek = []

    dlugosc = 30

    response = requests.get(f"https://api-fxpractice.oanda.com/v3/instruments/{paraWalutowa}/candles?count={dlugosc}&price=M&granularity={timeFrame}", headers=headers)

    for i in range(0, dlugosc):
        zamkSwieczki = response.json()['candles'][i]['mid']['c']
        zamkSwieczki = float(zamkSwieczki)
        zamknieciaSwieczek.append(zamkSwieczki)

    dl = 30

    hma = hull_moving_average(zamknieciaSwieczek, dlugosc)
    hma = round(hma, 5)
    print(hma)



def main():
    hekinBreakout()


if __name__ == '__main__':
    main()