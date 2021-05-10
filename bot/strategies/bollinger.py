"""Applies the Bollinger stategory on a collection of closing prices."""

import numpy as np
import pandas as pd
try:
    from .strategy_base import Strategy
except ImportError:
    from strategy_base import Strategy


class Bollinger(Strategy):
    """Applies the Bollinger stategory onto a collection of closing prices."""

    def apply_indicator(
        self,
        npCloses: np.array,
        config: dict,
        coinsOwned: bool,
    ) -> dict:

        period = config['period']

        # Edgecase
        if len(npCloses) < period + 1:
            return {
                'results': {
                    'Bollinger Low': '',
                    'Bollinger High': '',
                    'Bollinger Decision': 0
                },
                'decision': 0
            }

        # Convert the closing prices into a Pandas dataframe and add columns
        # with certain statistical information that will help calculate the
        # Bollinger value.
        npCloses = npCloses[-period - 1:]
        df = pd.DataFrame(npCloses, columns=['Close'])

        df['SMA'] = df['Close'].rolling(window=period).mean()
        df['STD'] = df['Close'].rolling(window=period).std()
        df['Upper'] = df['SMA'] + (df['STD'] * 2)
        df['Lower'] = df['SMA'] - (df['STD'] * 2)

        self.log(f'BOLLINGER: Upper={df["Upper"].iat[-1]}\
            Lower={df["Lower"].iat[-1]}')

        # Calculate buy/sell signals.
        if df['Close'].iat[-1] > df['Upper'].iat[-1] and coinsOwned:
            self.log('BOLLINGER: SELL')
            decision = -1

        elif df['Close'].iat[-1] < df['Lower'].iat[-1] and not coinsOwned:
            self.log('BOLLINGER: BUY')
            decision = 1

        else:
            decision = 0

        return {
            'results': {
                'Bollinger Low': df['Lower'].iat[-1],
                'Bollinger High': df['Upper'].iat[-1],
                'Bollinger Decision': decision
            },
            'decision': decision
        }


if __name__ == '__main__':
    import os
    print(os.path.abspath('.'))
    data = np.genfromtxt(os.path.join('test_data', 'closing_prices.csv'))

    phasedData = []
    coinsOwned = False
    for d in data:
        phasedData.append(float(d))
        results = Bollinger().apply_indicator(
            np.array(phasedData),
            {'period': 20},
            coinsOwned
        )
        print(f"{results['results']['Bollinger Low']}|{results['results']['Bollinger High']}|{results['results']['Bollinger Decision']}")
        if results['decision'] == 1:
            coinsOwned = True
        elif results['decision'] == -1:
            coinsOwned = False
