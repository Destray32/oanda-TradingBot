import sys

sys.path.append('E:\\vscode-projekty\\oanda-tradingBot\\pobieranie')
from pobieranieDanych import PobranieDanych


from numpy import cumsum, log, polyfit, sqrt, std, subtract


def hurst(ts):
    """Returns the Hurst Exponent of the time series vector ts"""
    # Create the range of lag values
    lags = range(2, 100)

    # Calculate the array of the variances of the lagged differences
    tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in lags]

    # Use a linear fit to estimate the Hurst Exponent
    poly = polyfit(log(lags), log(tau), 1)

    # Return the Hurst exponent from the polyfit output
    return poly[0]*2.0

data = PobranieDanych()
data = data['Close']
data = data.to_numpy()
print(hurst(data))

