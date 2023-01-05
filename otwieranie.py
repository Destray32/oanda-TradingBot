import requests


def Kupowanie(czyOtwarta, body, headers, ACCOUNT_ID):
    """
    Otwiera pozycje kupna jeśli nie ma otwartych pozycji
    """
    if (czyOtwarta == False):
        res = requests.post(f"https://api-fxpractice.oanda.com/v3/accounts/{ACCOUNT_ID}/orders", headers=headers, data=body)
        # print(res.json())
        # print (res.status_code)
        print("Kupiono")
    else:
        print("Nie można kupić ponieważ jest otwarta pozycja")

## Otwiera pozycje sprzedaży jeśli nie ma otwartych pozycji
def Sprzedawanie(czyOtwarta, body, headers, ACCOUNT_ID):
    """
    Otwiera pozycje sprzedazy jeśli nie ma otwartych pozycji
    """
    if (czyOtwarta == False):
        res = requests.post(f"https://api-fxpractice.oanda.com/v3/accounts/{ACCOUNT_ID}/orders", headers=headers, data=body)
        # print(res.json())
        # print (res.status_code)
        print("Sprzedano")
    else:
        print("Nie można sprzedać ponieważ jest otwarta pozycja")