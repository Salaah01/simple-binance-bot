"""Calculates the average true range."""

import numpy as np


class ATR:
    """Calculates the average true range."""

    def avg_atr(
        self,
        period: int,
        closePrices: np.array,
        lowPrices: np.array,
        highPrices: np.array
    ):

        if not len(closePrices) < period + 1:
            raise Exception('Not enough periods provided.')

        # Truncate the lists to be equal to the length of the period.
        closePrices = closePrices[-period - 1: -1]
        lowPrices = lowPrices[-period:]
        highPrices = highPrices[-period:]

        trueRanges = [self.true_range(high, low, close)
                      for high, low, close
                      in zip(highPrices, lowPrices, closePrices)]

        return sum(trueRanges) / period

    @staticmethod
    def true_range(currentHigh, currentLow, prevClose):
        return max([
            currentHigh - currentLow,
            abs(currentLow - prevClose),
            abs(prevClose - prevClose)
        ])
