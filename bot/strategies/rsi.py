from typing import Callable, Optional
import talib
import numpy as np


def rsi(
    npCloses: np.array,
    period: int,
    overboughtLimit: float,
    oversoldLimit: float,
    coinsOwned: bool,
    log: Optional[Callable],
) -> int:

    if not log:
        def log(msg):
            print(msg)

    if len(npCloses) < period:
        return 0

    rsi = talib.RSI(npCloses, period)
    lastRSI = rsi[-1]
    log(f'RSI: {lastRSI}')

    if lastRSI >= overboughtLimit and coinsOwned:
        log('RSI: SELL')
        return -1

    elif lastRSI <= oversoldLimit and not coinsOwned:
        log('RSI: BUY')
        return 1

    else:
        return 0
