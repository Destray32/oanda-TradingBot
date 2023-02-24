import sys
import numpy as np
import statsmodels.api as sm
import statsmodels

sys.path.append('E:\\vscode-projekty\\oanda-tradingBot\\pobieranie')
from pobieranieDanych import PobranieDanych

dane = PobranieDanych()

z_lag = np.roll(dane, 1)
z_lag[0] = 0
z_ret = dane - z_lag
z_ret[0] = 0

z_lag2 = sm.add_constant(z_lag)

model = statsmodels.regression.linear_model.OLS(z_ret, z_lag2)
results = model.fit()


halflife = abs(-np.log(2) / results.params[1][1])
print(halflife)
