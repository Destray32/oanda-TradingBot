import requests
import json
import threading
import datetime
import os


from otwieranie import Kupowanie, Sprzedawanie
from zamykanie import ZamknijPoz

# TODO: INFO - pozmieniałem sposób sprawdzania otwartych pozycji i warunek wejscia na pozycje dla long i short
# TODO: Zmienić sposób zamyniakia pozycji:
# Jesli jestesmy na długiej pozycji to zamykamy ją gdy świeczka zamknie się jako czerwona i na odwrót
# dla pozycji krótkiej

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
bodyBuy = f'{{"order": {{"units": "10000","instrument": "{paraWalutowa}","timeInForce": "FOK","type": "MARKET","positionFill": "DEFAULT"}}}}'
bodySell = f'{{"order": {{"units": "-10000","instrument": "{paraWalutowa}","timeInForce": "FOK","type": "MARKET","positionFill": "DEFAULT"}}}}'
bodyCloseLong = '{"longUnits": "ALL"}'
bodyCloseShort = '{"shortUnits": "ALL"}'


headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {ACCESS_TOKEN}',
}

def LiczenieMA(movingAV, dlugosc):
    movingAV /= dlugosc
    # movingAV = round(movingAV, 3)

    return movingAV

# funkcja sprawdza czy istnieje otwarta pozycja zwraca True lub False
def sprawdzOtwartePoz():
    res = requests.get(f"https://api-fxpractice.oanda.com/v3/accounts/{ACCOUNT_ID}/openPositions", headers=headers)

    pozycje = res.json()
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
    global sprzedane
    global kupione
    global bodyBuy
    global bodySell
    global bodyCloseLong
    global bodyCloseShort
    global paraWalutowa
    global oczekiwanieNaPrzeciecie

    bodyBuyText = json.loads(bodyBuy)
    bodyBuyText = json.dumps(bodyBuyText)

    bodySellText = json.loads(bodySell)
    bodySellText = json.dumps(bodySellText)

    bodyCloseLongText = json.loads(bodyCloseLong)
    bodyCloseLongText = json.dumps(bodyCloseLongText)

    bodyCloseShortText = json.loads(bodyCloseShort)
    bodyCloseShortText = json.dumps(bodyCloseShortText)


    if ((przedOstatnia < movingAV) and (ostatnia < movingAV) and sprzedane == False):
        print(sprzedane, kupione)
        if (kupione == True):
            # TODO: przetestować czy te zamykanie dobrze działa gdy rynek bedzie otwarty
            ZamknijPoz(ACCOUNT_ID, headers, bodyCloseLongText, bodyCloseShortText, paraWalutowa=paraWalutowa)

            czyOtwarda = sprawdzOtwartePoz()

            Sprzedawanie(czyOtwarda, bodySellText, headers, ACCOUNT_ID)
            data = datetime.datetime.now()
            print(str("Zmiana pozycji na sprzedaj: " + str(data)))

            kupione = False
            sprzedane = True
            oczekiwanieNaPrzeciecie = False
        else:
            czyOtwarda = sprawdzOtwartePoz()

            Sprzedawanie(czyOtwarda, bodySellText, headers, ACCOUNT_ID)
            data = datetime.datetime.now()
            print(str("Sprzedaj: " + str(data)))

            sprzedane = True
            oczekiwanieNaPrzeciecie = False
        return
    
    if ((przedOstatnia > movingAV) and (ostatnia > movingAV) and kupione == False):
        print(sprzedane, kupione)
        if (sprzedane == True):
            # TODO: przetestować czy te zamykanie dobrze działa gdy rynek bedzie otwarty
            ZamknijPoz(ACCOUNT_ID, headers, bodyCloseLongText, bodyCloseShortText, paraWalutowa=paraWalutowa)

            czyOtwarda = sprawdzOtwartePoz()

            Kupowanie(czyOtwarda, bodyBuyText, headers, ACCOUNT_ID)
            data = datetime.datetime.now()
            print(str("Zmiana pozycji na kup: " + str(data)))

            sprzedane = False
            kupione = True
            oczekiwanieNaPrzeciecie = False
        else:
            czyOtwarda = sprawdzOtwartePoz()

            Kupowanie(czyOtwarda, bodyBuyText, headers, ACCOUNT_ID)
            data = datetime.datetime.now()
            print(str("Kup: " + str(data)))

            kupione = True
            oczekiwanieNaPrzeciecie = False
        return

    ## nowy kod - rozpoznawanie wychamowywania trendu i wracanie spowortem gdy wychamowywanie 
    # jest falszywe - wersja eksperymentalna

    if (kupione == True and sprzedane == False and oczekiwanieNaPrzeciecie == False):
        if ((przedPrzedOstatnia > przedOstatnia) and (przedOstatnia > ostatnia)):
            ZamknijPoz(ACCOUNT_ID, headers, bodyCloseLongText, bodyCloseShortText, paraWalutowa=paraWalutowa)
            oczekiwanieNaPrzeciecie = True
            data = datetime.datetime.now()
            print ("Zamknieto pozycje ze wzgledu na hamujacy trend" + str(data))
    if (sprzedane == True and kupione == False and oczekiwanieNaPrzeciecie == False):
        if ((przedPrzedOstatnia < przedOstatnia) and (przedOstatnia < ostatnia)):
            ZamknijPoz(ACCOUNT_ID, headers, bodyCloseLongText, bodyCloseShortText, paraWalutowa=paraWalutowa)
            oczekiwanieNaPrzeciecie = True
            data = datetime.datetime.now()
            print ("Zamknieto pozycje ze wzgledu na hamujacy trend" + str(data))

        ### tu sie dzieja grube rzeczy jesli to bym zostawil ###

    ############################################################################################################

    # if (oczekiwanieNaPrzeciecie == True):
    #     if (kupione == True):
    #         if (przedPrzedOstatnia < przedOstatnia and przedOstatnia < ostatnia):
    #             czyOtwarda = sprawdzOtwartePoz()

    #             Kupowanie(czyOtwarda, bodyBuyText, headers, ACCOUNT_ID)
    #             data = datetime.datetime.now()
    #             print(str("Kup wywołane z hamujacym trendem: " + str(data)))

    #             oczekiwanieNaPrzeciecie = False
    #     if (sprzedane == True):
    #         if (przedPrzedOstatnia > przedOstatnia and przedOstatnia > ostatnia):
    #             czyOtwarda = sprawdzOtwartePoz()

    #             Sprzedawanie(czyOtwarda, bodySellText, headers, ACCOUNT_ID)
    #             data = datetime.datetime.now()
    #             print(str("Sprzedaj wywołane z hamujacym trendem: " + str(data)))

    #             oczekiwanieNaPrzeciecie = False




def hekinBreakout():
    # odpala funkcje w nowym watku. Funkcja sie nie chainuje wiec nie będzie błędów. Wykonuje się co 2 sekundy
    threading.Timer(2.0, hekinBreakout).start()

    global paraWalutowa

    heikinAshi = []
    timeFrame = "M15"

    movingAV = 0
    dlugosc = 21

    kupione = False
    sprzedane = False

    godzina = datetime.datetime.now().hour

    response = requests.get(f"https://api-fxpractice.oanda.com/v3/instruments/{paraWalutowa}/candles?count={dlugosc}&price=M&granularity={timeFrame}", headers=headers)

    for i in range(0, dlugosc):

        # kalkulowanie Heikin Ashi
        heikinClose = (float(response.json()['candles'][i]['mid']['h']) + 
                        float(response.json()['candles'][i]['mid']['l']) + 
                        float(response.json()['candles'][i]['mid']['c']) + 
                        float(response.json()['candles'][i]['mid']['o'])) / 4

        # heikinClose = round(heikinClose, 3)
        heikinAshi.append(heikinClose)

        movingAV += heikinClose
 
    movingAV = LiczenieMA(movingAV, dlugosc)

    # przed ostatni heikinClose
    przedOstatnia = heikinAshi[-2]
    # ostatni heikinClose
    ostatnia = heikinAshi[-1]

    przedPrzedOstatnia = heikinAshi[-3]

    # print("Heikin Ashi: ", heikinAshi)
    # print("Moving Average: ", movingAV)
    # print("Przedostatnia: ", przedOstatnia)
    # print("Ostatnia: ", ostatnia)

    if (godzina < 23 and godzina > 9):
        transakcja(przedPrzedOstatnia=przedPrzedOstatnia, przedOstatnia=przedOstatnia, ostatnia=ostatnia, movingAV=movingAV)
    else:
        print("Rynek nie płynny. Bot nie bedzie handlowac")



def main():
    hekinBreakout()


if __name__ == '__main__':
    main()