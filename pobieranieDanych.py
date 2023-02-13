from os import environ
import requests
import pandas as pd

ACCESS_TOKEN = environ.get('ACCESS_TOKEN')
ACCOUNT_ID = environ.get('ACCOUNT_ID')

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {ACCESS_TOKEN}',
}

def PobranieDanych():
    paraWalutowa = "EUR_USD"
    dlugosc = 2000
    timeFrame = "M1"

    response = requests.get(f"https://api-fxpractice.oanda.com/v3/instruments/{paraWalutowa}/candles?count={dlugosc}&price=M&granularity={timeFrame}", headers=headers)

    swieczki = response.json()['candles']
    df = pd.DataFrame(swieczki)
    df.rename(columns={'time': 'Date'}, inplace=True)
    df.drop(['complete'], axis=1, inplace=True)
    df.drop(['volume'], axis=1, inplace=True)

    czas = df['Date']
    data = df['mid']


    df = pd.DataFrame.from_records(data)
    df = df.rename(columns={'o': 'Open', 'h': 'High', 'l': 'Low', 'c': 'Close'})

    df = df.astype(float)
    df.set_index(pd.to_datetime(czas), inplace=True)

    data = df

    return data
