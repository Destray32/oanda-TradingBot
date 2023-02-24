import requests
import json
import threading
import datetime
import os
import talib as ta

import pandas as pd


from otwieranie import Kupowanie, Sprzedawanie
from zamykanie import ZamknijPoz
from pobieranie.pobieranieDanych import PobranieDanych

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
global czyWystopowany
global czyNowaSwieca
global kopiaOstatniej
paraWalutowa = "EUR_USD"
kupione = False
sprzedane = False
oczekiwanieNaPrzeciecie = False
kWieksze = True
dWieksze = False
czyWystopowany = False
czyNowaSwieca = False
kopiaOstatniej = 0

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
            # print("Jest otwarta pozycja")
            return True
        else:
            # print("Nie ma otwartych pozycji")
            return False

def transakcjaKup(ostatnia):
    global kupione
    global czyWystopowany

    bodyCloseLongText = json.loads(bodyCloseLong)
    bodyCloseLongText = json.dumps(bodyCloseLongText)

    czyOtwarta = sprawdzOtwartePoz()

    if (czyOtwarta == False):
        # Teoria do przetestowania, jesli pozycja nie jest otwarta a było coś kupione to znaczy
        # że pozycja dostała stop lossa
        if (kupione == True):
            czyWystopowany = True
            kupione = False
        else:
            czyWystopowany = False
            kupione = False

    if (kupione == False and czyOtwarta == False):
        ostatnia2 = ostatnia + 0.011
        ostatnia2 = round(ostatnia2, 5)

        ostatnia3 = ostatnia - 0.004
        ostatnia3 = round(ostatnia3, 5)

        bodyBuy = f'{{"order": {{"units": "10000","instrument": "{paraWalutowa}","timeInForce": "GTC", "type": "LIMIT", "price": "{ostatnia2}", "takeProfitOnFill": {{"price": "{ostatnia2}", "TimeInForce": "GTC" }}, "stopLossOnFill": {{"price": "{ostatnia3}", "TimeInForce": "GTC" }}}}}}'

        bodyBuyText = json.loads(bodyBuy)
        bodyBuyText = json.dumps(bodyBuyText)

        status = Kupowanie(czyOtwarta, bodyBuyText, headers, ACCOUNT_ID)
        if (status):
            kupione = True

    return

def transakcjaSprzedaj(ostatnia):
    global sprzedane
    global czyWystopowany

    bodyCloseShortText = json.loads(bodyCloseShort)
    bodyCloseShortText = json.dumps(bodyCloseShortText)

    czyOtwarta = sprawdzOtwartePoz()

    if (czyOtwarta == False):
    # Teoria do przetestowania, jesli pozycja nie jest otwarta a było coś kupione to znaczy
    # że pozycja dostała stop lossa
        if (sprzedane == True):
            czyWystopowany = True
            sprzedane = False
        else:
            czyWystopowany = False
            sprzedane = False

    if (sprzedane == False and czyOtwarta == False):
        ostatnia2 = ostatnia - 0.00011
        ostatnia2 = round(ostatnia2, 5)

        ostatnia3 = ostatnia + 0.0005
        ostatnia3 = round(ostatnia3, 5)

        bodySell = f'{{"order": {{"units": "-10000","instrument": "{paraWalutowa}","timeInForce": "GTC", "type": "LIMIT", "price": "{ostatnia2}", "takeProfitOnFill": {{"price": "{ostatnia2}", "TimeInForce": "GTC" }}, "stopLossOnFill": {{"price": "{ostatnia3}", "TimeInForce": "GTC" }}}}}}'

        bodySellText = json.loads(bodySell)
        bodySellText = json.dumps(bodySellText)

        status = Sprzedawanie(czyOtwarta, bodySellText, headers, ACCOUNT_ID)
        if (status):
            sprzedane = True

    return


def hekinBreakout():
    # odpala funkcje w nowym watku. Funkcja sie nie chainuje wiec nie będzie błędów. Wykonuje się co 2 sekundy
    # threading.Timer(1.0, hekinBreakout).start()

    global paraWalutowa
    global kupione
    global sprzedane
    global kWieksze
    global dWieksze
    global czyNowaSwieca
    global kopiaOstatniej

    timeFrame = "M1"
    zamknieciaSwieczek = []

    # pobieranie danych
    dane = PobranieDanych()

    dane['ms'] = ta.CDLMORNINGSTAR(dane['Open'], dane['High'], dane['Low'], dane['Close'])
    dane['ms_d']= ta.CDLMORNINGDOJISTAR(dane['Open'], dane['High'], dane['Low'], dane['Close'])
    
    ostatnia = dane['Close'].iloc[-1]

    # TODO: sprawdzić czy dobrze kupuje według syngału.
    # w sensie czy musi być -2 czy -1 
    # TODO: ustawić dobrze stop loss i take profit w funkcji
    # if dane['ms'].iloc[-2] == 100 or dane['ms_d'].iloc[-2] == 100:
    #     transakcjaKup(ostatnia)

    


        
def main():
    hekinBreakout()


if __name__ == '__main__':
    main()