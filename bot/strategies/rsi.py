from typing import Callable, Optional
from collections import namedtuple
import talib
import numpy as np


def rsi(
    npCloses: np.array,
    period: int,
    overboughtLimit: float,
    oversoldLimit: float,
    coinsOwned: bool,
    log: Optional[Callable] = None,
) -> int:

    if not log:
        def log(msg):
            print(msg)

    outputFields = ['rsi', 'decision']

    if len(npCloses) < period:
        return namedtuple('rsi', outputFields)('', 0)

    rsi = talib.RSI(npCloses, period)
    lastRSI = rsi[-1]
    log(f'RSI: {lastRSI}')

    if lastRSI >= overboughtLimit and coinsOwned:
        log('RSI: SELL')
        return namedtuple('rsi', outputFields)(lastRSI, -1)

    elif lastRSI <= oversoldLimit and not coinsOwned:
        log('RSI: BUY')
        return namedtuple('rsi', outputFields)(lastRSI, 1)

    else:
        return namedtuple('rsi', outputFields)(lastRSI, 0)
