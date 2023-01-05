import requests

def ZamknijPoz(ACCOUNT_ID, headers, bodyCloseLongText, bodyCloseShortText, paraWalutowa):
    """
    Zamyka pozycje kupna lub sprzedazy. Zamyka wszystkie pozycje kupna lub sprzedazy
    """

    # TODO: pare walutowa przekazywac przez argument
    res = requests.put(f"https://api-fxpractice.oanda.com/v3/accounts/{ACCOUNT_ID}/positions/{paraWalutowa}/close", headers=headers, data=bodyCloseShortText)
    # print(res.json())
    # print (res.status_code)

    res = requests.put(f"https://api-fxpractice.oanda.com/v3/accounts/{ACCOUNT_ID}/positions/{paraWalutowa}/close", headers=headers, data=bodyCloseLongText)
    # print(res.json())
    # print (res.status_code)
