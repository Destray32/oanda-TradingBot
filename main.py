import requests
import json
import threading
import datetime
import os
import talib

import pandas as pd


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
global kWieksze
global dWieksze
paraWalutowa = "EUR_USD"
kupione = False
sprzedane = False
oczekiwanieNaPrzeciecie = False
kWieksze = True
dWieksze = False

# body do kupowania waluty
bodyCloseLong = '{"longUnits": "ALL"}'
bodyCloseShort = '{"shortUnits": "ALL"}'

# body do kupowania waluty


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

def transakcja(ostatnia):
    global kupione

    bodyCloseLongText = json.loads(bodyCloseLong)
    bodyCloseLongText = json.dumps(bodyCloseLongText)

    czyOtwarta = sprawdzOtwartePoz()

    if (czyOtwarta == False):
        kupione = False

    if (kupione == False and czyOtwarta == False):
        ostatnia2 = ostatnia + 0.0011
        ostatnia2 = round(ostatnia2, 5)

        ostatnia3 = ostatnia - 0.0005
        ostatnia3 = round(ostatnia3, 5)

        bodyBuy = f'{{"order": {{"units": "10000","instrument": "{paraWalutowa}","timeInForce": "GTC", "type": "LIMIT", "price": "{ostatnia2}", "takeProfitOnFill": {{"price": "{ostatnia2}", "TimeInForce": "GTC" }}, "stopLossOnFill": {{"price": "{ostatnia3}", "TimeInForce": "GTC" }}}}}}'

        bodyBuyText = json.loads(bodyBuy)
        bodyBuyText = json.dumps(bodyBuyText)

        status = Kupowanie(czyOtwarta, bodyBuyText, headers, ACCOUNT_ID)
        if (status):
            kupione = True

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

def kierunekPrzeciecia(liniaK, liniaD):
    """
    Sprawdza kierunek w jakim przecięty jest wskaźnik stochastic. \n
    \t 1 = przecięty w góre 0 = przecięty w dół
    """

    if (liniaK > liniaD):
        return 1
    elif(liniaK < liniaD):
        return 0

def sygnalStoch(kierunekPrzeciecia, liniaK, liniaD):
    """
    Funkcja sprawdzajaca czy warunki na wskazniku stochastic sa sprzyjajace zawarciu transakcji
    """
    if(kierunekPrzeciecia == 1 and liniaK < 50.0 and liniaD < 50.0):
        return True
    else:
        return False

def sygnalHull(hma, przedOst, ostatnia):
    """
    Funckja sprawdza czy przed ostatnie zamkniecie swieczki i ostatnie zamkniecie znajduje sie /t
    ponad wskaznikiem HMA
    """
    if(przedOst > hma and ostatnia > hma):
        return True
    else:
        return False

def sygnalSprzedaz(hma, przedOst, ostatnia):
    """
    Funckja sprawdza czy przed ostatnie zamkniecie swieczki i ostatnie zamkniecie znajduje sie /t
    pod wskaznikiem HMA. Nalezy wtedy zamknąć swoja pozycje
    """
    if(przedOst < hma and ostatnia < hma):
        return True
    else:
        return False


def hekinBreakout():
    # odpala funkcje w nowym watku. Funkcja sie nie chainuje wiec nie będzie błędów. Wykonuje się co 2 sekundy
    threading.Timer(2.0, hekinBreakout).start()

    global paraWalutowa
    global kupione
    global kWieksze
    global dWieksze

    timeFrame = "M15"
    zamknieciaSwieczek = []

    # na dlugosci 30 wskazniki dobrze dzialaja
    dlugosc = 30

    response = requests.get(f"https://api-fxpractice.oanda.com/v3/instruments/{paraWalutowa}/candles?count={dlugosc}&price=M&granularity={timeFrame}", headers=headers)

    for i in range(0, dlugosc):
        zamkSwieczki = response.json()['candles'][i]['mid']['c']

        zamkSwieczki = float(zamkSwieczki)
        zamknieciaSwieczek.append(zamkSwieczki)


    hma = hull_moving_average(zamknieciaSwieczek, dlugosc)
    hma = round(hma, 5)
    # print(hma)

    # make a panadas dataframe with the data from the API
    df = pd.DataFrame(response.json()['candles'])
    
    # convert df to floats
    df['mid'] = df['mid'].apply(lambda x: {k: float(v) for k, v in x.items()})

    df['14-low'] = df['mid'].apply(lambda x: x['l']).rolling(window=14).min()
    df['14-high'] = df['mid'].apply(lambda x: x['h']).rolling(window=14).max()
    df['%K'] = 100 * ((df['mid'].apply(lambda x: x['c']) - df['14-low']) / (df['14-high'] - df['14-low']))
    
    df['%K'] = talib.SMA(df['%K'], timeperiod=6)
    df['%D'] = df['%K'].rolling(window=3).mean()

    liniaK = df['%K'][dlugosc-1]
    liniaD = df['%D'][dlugosc-1]

    # wychwytywanie przecięcia lini stochastic
    if (df['%K'][29] > df['%D'][29] and dWieksze == True):
        data = datetime.datetime.now()
        kWieksze = True
        dWieksze = False
        print("Przecięcie stochastic: ", data)
    elif(df['%K'][29] < df['%D'][29] and kWieksze == True):
        data = datetime.datetime.now()
        print("Przecięcie stochastic: ", data)
        dWieksze = True
        kWieksze = False

    kierunekStoch = kierunekPrzeciecia(liniaK, liniaD)
    sSto = sygnalStoch(kierunekStoch, liniaK, liniaD)
    sHull = sygnalHull(hma, zamknieciaSwieczek[-2], zamknieciaSwieczek[-1])
    sSprzedaz = sygnalSprzedaz(hma, zamknieciaSwieczek[-2], zamknieciaSwieczek[-1])
    
    if (sSto and sHull and sSprzedaz == False):
        # date = datetime.datetime.now()
        # print("Warunki do kupienia: ", date)

        transakcja(zamknieciaSwieczek[-1])

    if (sSprzedaz == True):
        bodyCloseLongText = json.loads(bodyCloseLong)
        bodyCloseLongText = json.dumps(bodyCloseLongText)

        bodyCloseShortText = json.loads(bodyCloseShort)
        bodyCloseShortText = json.dumps(bodyCloseShortText)

        ZamknijPoz(ACCOUNT_ID, headers, bodyCloseLongText, bodyCloseShortText, paraWalutowa)
        kupione = False

        
def main():
    hekinBreakout()


if __name__ == '__main__':
    main()