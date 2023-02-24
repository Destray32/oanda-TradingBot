from pobieranie.pobieranieDanych import PobranieDanych

def chiko_span(data):
    return data.Close.shift(-1)

def main():
    dane = PobranieDanych()
    chiko_data = chiko_span(dane)


    zamk = dane['Close'].iloc[-3]
    chiko = chiko_data.iloc[-3]
    print(zamk, chiko)


if __name__ == '__main__':
    main()