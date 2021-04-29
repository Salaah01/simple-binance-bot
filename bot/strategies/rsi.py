from typing import Callable, Optional
import talib
import numpy as np


def rsi(
    npCloses: np.array,
    period: int,
    overboughtLimit: float,
    oversoldLimit: float,
    coinOwned: bool,
    log: Optional[Callable] = lambda msg: print(msg)
) -> bool:
    if len(npCloses) < period:
        return 0

    rsi = talib.RSI(npCloses, period)
    lastRSI = rsi[-1]
    log(f'RSI: {lastRSI}')

    if lastRSI >= overboughtLimit and ownCoins:
        log('RSI: BUY')
        return -1

    if lastRSI <= oversoldLimit and not self.ownCoins:
        log('RSI: BUY')
        return 1
