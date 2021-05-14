"""Calculates the Keltner Channels."""


from collections import namedtuple
import numpy as np

try:
    from .strategy_base import Strategy
    from .ema import EMA
    from .atr import ATR
except ImportError:
    from strategy_base import Strategy
    from ema import EMA
    from atr import ATR


class KeltnerChannels(Strategy):
    """Calculates the Keltner Channels."""

    def apply_indicator(
        self,
        closePrices: np.array,
        config: dict,
        coinsOwned: bool,
        lowPrices: np.array,
        highPrices: np.array
    ) -> dict:
        """Calculates the Keltner Channels and makes a decision on whether to
        buy/sell.

        Args:
            closePrices - (np.array) Collection of closing prices.
            config - (dict) Configurations.
            coinsOwned - (bool) Is the coin currently owned?
            lowPrices - (np.array) Collection of low prices.
            highPrices - (np.array) Collection of high prices.

        Returns:
            dict - Returns a `results` key containing printable results and a
                `decision` key which decides whether or not to buy/sell.
        """

        # Edgecase - if there is insufficient data, then do not proceed.
        if len(lowPrices) < max([config['ema_period'], config['atr_period']]):
            return {
                'results': {
                    'Keltner Channels Middle Line': '',
                    'Keltner Channels Lower Band': '',
                    'Keltner Channels Upper Band': '',
                    'Keltner Channels Decision': 0
                },
                'decision': 0
            }

        results = self.calculate(
            closePrices,
            lowPrices,
            highPrices,
            config['ema_period'],
            config['atr_period'],
            config['atr_multi']
        )

        if coinsOwned and closePrices[-1] >= results.upperBand:
            decision = -1
        elif not coinsOwned and closePrices[-1] <= results.lowerBand:
            decision = 1
        else:
            decision = 0

        return {
            'results': {
                'Keltner Channels Middle Line': results.middleLine,
                'Keltner Channels Lower Band': results.lowerBand,
                'Keltner Channels Upper Band': results.upperBand,
                'Keltner Channels Decision': decision
            },
            'decision': decision
        }

    @staticmethod
    def calculate(
        closePrices: np.array,
        lowPrices: np.array,
        highPrices: np.array,
        emaPeriod: int,
        atrPeriod: int,
        atrMulti: float
    ) -> dict:
        """Calculate the Keltner Channels over a period.

        Args:
            closePrices - (np.array) Collection of closing prices.
            lowPrices - (np.array) Collection of candle low prices.
            highPrices - (np.array) Collection of candle high prices.
            emaPeriod - (int) EMA period.
            atrPeriod - (int) ATR period.
            atrMulti - (float) Multiplier for the ATR value.

        Returns:
            namedtuple - Returns the lower amd middle bands and middle line.
        """
        emas = EMA().calc_ema(closePrices, emaPeriod)
        atr = ATR().avg_atr(atrPeriod, closePrices, lowPrices, highPrices)

        latestEMA = emas.iloc[-1]
        return namedtuple(
            'KeltnerChannels',
            ['middleLine', 'upperBand', 'lowerBand']
        )(latestEMA, latestEMA + atrMulti*atr, latestEMA - atrMulti * atr)


if __name__ == '__main__':
    config = {
        "ema_period": 5,
        "atr_period": 5,
        "atr_multi": 2
    }

    kc = KeltnerChannels().apply_indicator(
        np.array([100, 200, 300, 400, 500, 600, 700, 800, 900, 10, 11, 12, 13,
                  14, 15, 16]),
        config,
        False,
        np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]),
        np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]),
    )

    print(kc)
