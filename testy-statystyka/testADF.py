import sys
import statsmodels.tsa.stattools as ts

sys.path.append('E:\\vscode-projekty\\oanda-tradingBot\\pobieranie')
from pobieranieDanych import PobranieDanych


data = PobranieDanych()


adf = ts.adfuller(data['Close'], 1)
print(adf)