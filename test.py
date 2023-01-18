

def weighted_moving_average(series, lookback = None) -> float:
    if not lookback:
        lookback = len(series)
    if len(series) == 0:
        return 0
    assert 0 < lookback <= len(series)

    wma = 0
    lookback_offset = len(series) - lookback
    for index in range(lookback + lookback_offset - 1, lookback_offset - 1, -1):
        weight = index - lookback_offset + 1
        wma += series[index] * weight
    return wma / ((lookback ** 2 + lookback) / 2)


def hull_moving_average(series: list[float], lookback: int) -> float:
    assert lookback > 0
    hma_series = []
    for k in range(int(lookback ** 0.5), -1, -1):
        s = series[:-k or None]
        wma_half = weighted_moving_average(s, min(lookback // 2, len(s)))
        wma_full = weighted_moving_average(s, min(lookback, len(s)))
        hma_series.append(wma_half * 2 - wma_full)
    return weighted_moving_average(hma_series)

zamknieciaSwieczek = [1.345, 1.445, 1.545, 1.645, 1.745, 1.845, 1.945, 2.045, 2.145, 2.245, 2.345, 2.445, 2.545, 2.645, 2.745, 2.845, 2.945, 3.045, 3.145, 3.245, 3.345, 3.445, 3.545, 3.645, 3.745, 3.845, 3.945, 4.045, 4.145, 4.245]

hma = hull_moving_average(zamknieciaSwieczek, 3)
print(hma)