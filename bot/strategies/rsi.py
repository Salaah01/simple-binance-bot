from typing import Callable, Optional
from collections import namedtuple
import numpy as np


def rsi(
    npCloses: np.array,
    period: int,
    overboughtLimit: float,
    oversoldLimit: float,
    coinsOwned: bool,
    log: Optional[Callable] = None,
) -> namedtuple:
    """Method for calculating RSI for a collection of prices.

    Args:
        npCloses - (numpy.array) Collection of prices.
        period - (int) RSI period.
        overboughtLimit - (float) The upper bound indicating where the asset
            has been overbought.
        overboughtLimit - (float) The lower bound indicating where the asset
            has been oversold.
        coinsOwned - (bool) Do we currently own some of the coin (asset)?
        log - (function) A function to log the result.

    Returns
        namedtuple
            rsi - (float) RSI value
            decision - (int) 1=Buy, 0=Do nothing, -1=Sell
    """

    if not log:
        def log(msg):
            print(msg)

    outputFields = ['rsi', 'decision']

    if len(npCloses) < period:
        return namedtuple('rsi', outputFields)('', 0)

    gains = []
    loses = []
    avgGains = []
    avgLosses = []
    relativeStrength = []
    relativeStrengthIndex = []

    if len(npCloses) >= 3 * period:
        npCloses = npCloses[-(3*period):]

    for c in range(1, len(npCloses)):
        # Check gains / loses
        if npCloses[c] >= npCloses[c-1]:
            gains.append(npCloses[c] - npCloses[c-1])
            loses.append(0)
        else:
            loses.append(npCloses[c-1] - npCloses[c])
            gains.append(0)

        # Check average gains / loses
        if c == period:
            avgGains.append(sum(gains) / period)
            avgLosses.append(sum(loses) / period)
        elif c > period:
            avgGains.append(((avgGains[-1]*(period-1)+gains[-1])/period))
            avgLosses.append(((avgLosses[-1]*(period-1)+loses[-1])/period))

        # Calculates RS and RSI value
        if c >= period:
            relativeStrength.append(avgGains[-1]/avgLosses[-1])
            relativeStrengthIndex.append(
                100 - (100 / (relativeStrength[-1] + 1)))

    rsiValue = relativeStrengthIndex[-1]

    log(f'RSI: {rsiValue}')

    if rsiValue >= overboughtLimit and coinsOwned:
        log('RSI: SELL')
        return namedtuple('rsi', outputFields)(rsiValue, -1)

    elif rsiValue <= oversoldLimit and not coinsOwned:
        log('RSI: BUY')
        return namedtuple('rsi', outputFields)(rsiValue, 1)

    else:
        return namedtuple('rsi', outputFields)(rsiValue, 0)


if __name__ == "__main__":
    prices = np.array([2385.66, 2390.42, 2383.49, 2380.64, 2380.16, 2377.89,
                      2388.82, 2385.05, 2392.36, 2391.36, 2387.55, 2387.67,
                      2395.96, 2398.47])
    period = 6
    overboughtLimit = 70.0
    oversoldLimit = 30.0
    coinsOwned = True

    rsi(prices, period, overboughtLimit, oversoldLimit, coinsOwned)
