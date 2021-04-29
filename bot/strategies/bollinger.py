from typing import Callable, Optional
import numpy as np
from talib import BBANDS


def bollinger(
    npCloses: np.array,
    period: int,
    nbdevup: int,
    nbdevdn: int,
    matype: int,
    coinsOwned: bool,
    log: Optional[Callable]
) -> int:
    if not log:
        def log(msg):
            print(msg)

    if len(npCloses) < period + 1:
        return 0

    up, mid, low = BBANDS(npCloses[:-1], period, nbdevup, nbdevdn, matype)
    bbp = (npCloses[-1] - low) / (up - low)
    log(f'BOLLINGER: BBP {bbp}')

    if npCloses[-1] > bbp[-1] and npCloses[-1] >= npCloses[-2] and not coinsOwned:
        log('BOLLINGER: BUY')
        return -1

    elif npCloses[-1] < bbp[-2] and npCloses[-1] <= npCloses[-2] and coinsOwned:
        log('BOLLINGER: SELL')
        return 1

    else:
        return 0
