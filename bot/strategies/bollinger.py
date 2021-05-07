"""Applies the Bollinger stategory on a collection of closing prices."""

from typing import Callable, Optional
from collections import namedtuple
import numpy as np
import pandas as pd
from strategy_base import Strategy


class Bollinger(Strategy):
    """Applies the Bollinger stategory on a collection of closing prices."""

    def apply_indicator(
        self,
        npCloses: np.array,
        period: int,
        coinsOwned: bool,
    ) -> dict:

        # Edgecase
        if len(npCloses) < period + 1:
            return {'results': {'low': '', 'high': ''}, 'decision': 0}

        df = pd.DataFrame(npCloses, columns=['Close'])

        df['SMA'] = df['Close'].rolling(window=period).mean()
        df['STD'] = df['Close'].rolling(window=period).std()
        df['Upper'] = df['SMA'] + (df['STD'] * 2)
        df['Lower'] = df['SMA'] - (df['STD'] * 2)

        self.log(f'BOLLINGER: Upper={df["Upper"].iat[-1]}\
            Lower={df["Lower"].iat[-1]}')

        # Calculate buy/sell signals.
        if df['Close'].iat[-1] > df['Upper'].iat[-1] * 0.9 and coinsOwned:
            self.log('BOLLINGER: SELL')
            return {
                'results': {
                    'low': df['Lower'].iat[-1],
                    'high': df['Upper'].iat[-1]
                },
                'decision': -1
            }

        elif df['Close'].iat[-1] < df['Lower'].iat[-1] and not coinsOwned:
            log('BOLLINGER: BUY')
            return namedtuple(
                'bollinger',
                outputFields
            )(df['Upper'].iat[-1], df['Lower'].iat[-1], 1)

        else:
            return namedtuple(
                'bollinger',
                outputFields
            )(df['Upper'].iat[-1], df['Lower'].iat[-1], 0)


def bollinger(
    npCloses: np.array,
    period: int,
    coinsOwned: bool,
    log: Optional[Callable]
) -> int:
    if not log:
        def log(msg):
            print(msg)

    outputFields = ['high', 'low', 'decision']

    if len(npCloses) < period + 1:
        return namedtuple('bollinger', outputFields)('', '', 0)

    df = pd.DataFrame(npCloses, columns=['Close'])

    # Calculate simple moving average, standard deviation, upper and lower
    # bands.
    df['SMA'] = df['Close'].rolling(window=period).mean()
    df['STD'] = df['Close'].rolling(window=period).std()
    df['Upper'] = df['SMA'] + (df['STD'] * 2)
    df['Lower'] = df['SMA'] - (df['STD'] * 2)

    log(f'BOLLINGER: Upper={df["Upper"].iat[-1]} Lower={df["Lower"].iat[-1]}')

    # Calculate buy/sell signals.
    if df['Close'].iat[-1] > df['Upper'].iat[-1] * 0.9 and coinsOwned:
        log('BOLLINGER: SELL')
        return namedtuple(
            'bollinger',
            outputFields
        )(df['Upper'].iat[-1], df['Lower'].iat[-1], -1)

    elif df['Close'].iat[-1] < df['Lower'].iat[-1] and not coinsOwned:
        log('BOLLINGER: BUY')
        return namedtuple(
            'bollinger',
            outputFields
        )(df['Upper'].iat[-1], df['Lower'].iat[-1], 1)

    else:
        return namedtuple(
            'bollinger',
            outputFields
        )(df['Upper'].iat[-1], df['Lower'].iat[-1], 0)
