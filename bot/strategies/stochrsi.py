"""Applies the Stochastic RSI strategy on a collection of closing prices."""

from collections import namedtuple
import numpy as np
import pandas as pd
try:
    from .strategy_base import Strategy
except ImportError:
    from strategy_base import Strategy


class StochRSI(Strategy):
    """Applies Stochastic RSI on a collection of closing prices."""

    def apply_indicator(
        self,
        closePrices: np.array,
        config: dict,
        coinsOwned: bool
    ) -> dict:
        """Calculates the Stochastic RSI and makes a decision on whether to
        buy/sell.

        Args:
            closePrices - (np.array) Collection of closing prices.
            config - (dict) Configurations.
            coinsOwned - (bool) Is the coin currently owned?

        Returns:
            dict - Returns a `results` key containing printable results and a
                `decision` key which decides whether or not to buy/sell.
        """

        # Parse the config and extract information that will be needed.
        period = config['period']
        overboughtLimit = config['overbought_limit']
        oversoldLimit = config['oversold_limit']

        # Edgecase to prevent innacuracy of results and preventing the usage
        # of Simple Moving Average over Exponential Moving Average.
        if len(closePrices) < period*2:
            return {
                'results': {'RSI Value': '', 'RSI Decision': 0},
                'decision': 0
            }

        closePrices = closePrices[-period*2:]

        stochRSIValue = self.calc_rsi(
            closePrices, period, smoothK=3, smoothD=3).stochrsi.iloc[-1]
        print(stochRSIValue)
        self.log(f'RSI: {stochRSIValue}')

        if stochRSIValue >= overboughtLimit and coinsOwned:
            self.log('RSI: SELL')
            decision = -1
        elif stochRSIValue <= oversoldLimit and not coinsOwned:
            self.log('RSI: BUY')
            decision = 1
        else:
            decision = 0

        return {
            'results': {'RSI Value': stochRSIValue, 'RSI Decision': decision},
            'decision': decision
        }

    @staticmethod
    def calc_rsi(
        closingPrices: np.array,
        period: int,
        smoothK: int,
        smoothD: int
    ) -> namedtuple:
        """Calculates the Stochastic RSI.

        Args:
            npCloses - (np.array) Collection of closing prices.
            period - (int) Period.
            smoothK - (int) - Mean of stochastic RSI values in list.
            smoothD - (int) - Mean of smoothK values in list.

        Returns:
            namedtuple - Stochastic RSI for `npCloses`.
        """

        prices = pd.Series(closingPrices)

        # Calculate the RSI
        delta = prices.diff().dropna()
        ups = delta * 0
        downs = ups.copy()
        ups[delta > 0] = delta[delta > 0]
        downs[delta < 0] = -delta[delta < 0]

        # first value is sum of avg gains
        ups[ups.index[period-1]] = np.mean(ups[:period])
        ups = ups.drop(ups.index[:(period-1)])

        # first value is sum of avg losses
        downs[downs.index[period-1]] = np.mean(downs[:period])
        downs = downs.drop(downs.index[:(period-1)])

        upsEwn = ups.ewm(com=period-1, min_periods=0, adjust=False,
                         ignore_na=False).mean()
        downsEwn = downs.ewm(com=period-1, min_periods=0, adjust=False,
                             ignore_na=False).mean()
        rs = upsEwn / downsEwn

        rsi = 100 - 100 / (1 + rs)

        # Calculate StochRSI
        stochrsi = ((rsi - rsi.rolling(period).min())
                    / (rsi.rolling(period).max() -
                    rsi.rolling(period).min())) * 100
        stochrsiK = stochrsi.rolling(smoothK).mean()
        stochrsiD = stochrsiK.rolling(smoothD).mean()

        return namedtuple(
            'stochRSI',
            ['stochrsi', 'stochrsiK', 'stochrsiD']
        )(stochrsi, stochrsiK, stochrsiD)