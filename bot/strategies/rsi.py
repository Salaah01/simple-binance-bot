from typing import Callable, Optional
from collections import namedtuple
import talib
import numpy as np
from .strategy_base import Strategy


class RSI(Strategy):
    """Applies the RSI strategy onto a collection of closing prices."""

    def apply_indicator(
        self,
        npCloses: np.array,
        config: dict,
        coinsOwned: bool
    ) -> dict:

        # Parse the config and extract information that will be needed.
        period = config['period']
        overboughtLimit = config['overbought_limit']
        oversoldLimit = config['oversold_limit']


        # Edgecase
        if len(npCloses) < period:
            return {'results': {'rsi': ''}, 'decision': 0}

        rsi = talib.RSI(npCloses, period)
        lastRSI = rsi[-1]
        self.log(f'RSI: {lastRSI}')

        if lastRSI >= overboughtLimit and coinsOwned:
            self.log('RSI: SELL')
            decision = -1
        elif lastRSI <= oversoldLimit and not coinsOwned:
            self.log('RSI: BUY')
            decision = 1
        else:
            decision = 0

        return {'results': {'rsi': lastRSI}, 'decision': decision}


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
