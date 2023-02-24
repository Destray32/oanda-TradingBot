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
global czyOtwarte
global czyZostaloZamkniete
global timerZamkniecia
paraWalutowa = "EUR_USD"
kupione = False
sprzedane = False
oczekiwanieNaPrzeciecie = False
kWieksze = True
dWieksze = False
czyWystopowany = False
czyNowaSwieca = False
kopiaOstatniej = 0
czyOtwarte = False
czyZostaloZamkniete = False
timerZamkniecia = 120

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
    print("Kupuje")
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
        ostatnia2 = ostatnia + 0.0020
        ostatnia2 = round(ostatnia2, 5)

        ostatnia3 = ostatnia - 0.00023
        ostatnia3 = round(ostatnia3, 5)

        bodyBuy = f'{{"order": {{"units": "2500","instrument": "{paraWalutowa}","timeInForce": "FOK","type": "MARKET","positionFill": "DEFAULT"}}}}'

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
    print(czyOtwarta)

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
        ostatnia2 = ostatnia - 0.0020
        ostatnia2 = round(ostatnia2, 5)

        ostatnia3 = ostatnia + 0.00023
        ostatnia3 = round(ostatnia3, 5)

        bodySell = f'{{"order": {{"units": "-2500","instrument": "{paraWalutowa}","timeInForce": "FOK","type": "MARKET","positionFill": "DEFAULT"}}}}'

        bodySellText = json.loads(bodySell)
        bodySellText = json.dumps(bodySellText)

        status = Sprzedawanie(czyOtwarta, bodySellText, headers, ACCOUNT_ID)
        if (status):
            sprzedane = True

    return


def hekinBreakout():
    # odpala funkcje w nowym watku. Funkcja sie nie chainuje wiec nie będzie błędów. Wykonuje się co 2 sekundy
    threading.Timer(1.0, hekinBreakout).start()

    global paraWalutowa
    global kupione
    global sprzedane
    global kWieksze
    global dWieksze
    global czyNowaSwieca
    global kopiaOstatniej
    global czyOtwarte
    global czyZostaloZamkniete
    global timerZamkniecia

    godzina = datetime.datetime.now().hour

    kopiaCzyOtwarte = czyOtwarte

    czyOtwarte = sprawdzOtwartePoz()

    # if (kopiaCzyOtwarte != czyOtwarte):
    #     if (czyOtwarte == False):
    #         czyZostaloZamkniete = True
    #         print("Pozycja została zamknięta")


    # if timerZamkniecia != 0 and czyZostaloZamkniete == True:
    #     timerZamkniecia = timerZamkniecia - 1
    #     print(timerZamkniecia)
    #     return
    # else:
    #     timerZamkniecia = 120
    #     czyZostaloZamkniete = False
        
        


    # pobieranie danych
    dane = PobranieDanych()
    closeWczorajStrat(dane, godzina, sprzedane, kupione)


############################################################################################################

def closeWczorajStrat(dane, godzina, sprzedane, kupione):
    ostatnia = dane['Close'].iloc[-1]
    przedostatnia = dane['Close'].iloc[-2]
    trzecia = dane['Close'].iloc[-3]

    if godzina >= 8 and godzina <= 22:
        # short pozycja
        if przedostatnia < trzecia:
            if kupione == True:
                ZamknijPoz(ACCOUNT_ID, headers, bodyCloseLong, bodyCloseShort, paraWalutowa)
                kupione = False
                transakcjaSprzedaj(ostatnia)
            else:
                transakcjaSprzedaj(ostatnia)
            
        # long pozycja
        if przedostatnia > trzecia:
            if sprzedane == True:
                ZamknijPoz(ACCOUNT_ID, headers, bodyCloseLong, bodyCloseShort, paraWalutowa)
                sprzedane = False
                transakcjaKup(ostatnia)
            else:
                transakcjaKup(ostatnia)
            


def boilingerSrat(dane, godzina):
    upper, middle, lower = ta.BBANDS(dane['Close'], timeperiod=10, nbdevup=2, nbdevdn=2, matype=0)
    dane['upper'] = upper
    dane['middle'] = middle
    dane['lower'] = lower
    
    ostatnia = dane['Close'].iloc[-1]
    przedostatnia = dane['Close'].iloc[-2]

    przedOstUpper = round(dane['upper'].iloc[-2], 5)
    przedOstMiddle = round(dane['middle'].iloc[-2], 5)
    przedOstLower = round(dane['lower'].iloc[-2], 5)

    # TODO: sprawdzić czy dobrze kupuje według syngału.
    # w sensie czy musi być -2 czy -1 
    # TODO: ustawić dobrze stop loss i take profit w funkcji

    if godzina >= 8 and godzina <= 22:
        # long pozycja
        if przedostatnia <= dane['lower'].iloc[-2] and czyOtwarte == False:
            transakcjaKup(ostatnia)

        # short pozycja
        if przedostatnia >= dane['upper'].iloc[-2] and czyOtwarte == False:
            transakcjaSprzedaj(ostatnia)

    # wyjscie z long pozycji
    if kupione == True and przedostatnia >= przedOstMiddle:
        ZamknijPoz(ACCOUNT_ID, headers, bodyCloseLong, bodyCloseShort, paraWalutowa)
        kupione = False

    # wyjscie z short pozycji
    if sprzedane == True and przedostatnia <= przedOstMiddle:
        ZamknijPoz(ACCOUNT_ID, headers, bodyCloseLong, bodyCloseShort, paraWalutowa)
        sprzedane = False


         
def main():
    hekinBreakout()


if __name__ == '__main__':
    main()