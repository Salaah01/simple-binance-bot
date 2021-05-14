import numpy as np
import pandas as pd


class EMA:
    """Uses a set of closing date to create an EMA."""

    @staticmethod
    def calc_ema(npCloses: np.array, period: int) -> pd.Series:
        """Calculates the EMA.

        Args:
            npCloses - (np.array) Collection of closing prices.
            period - (int) Period.

        Returns:
            pd.Series - EMAs for `npCloses`.
        """

        pricesSeries = pd.Series(npCloses)

        # For EMA, for anything before the `period` we calculate the simple
        # moving average (SMA). With the data past the period (`rest`), we use
        # the EMA calculation where for some elements, it will require the SMA.
        sma = pricesSeries.rolling(window=period).mean()[:period]
        rest = pricesSeries[period:]

        return pd.concat([sma, rest]).ewm(span=period, adjust=False).mean()


if __name__ == '__main__':
    e = EMA().calc_ema(np.array([2, 4, 6, 8, 12, 14, 16, 18, 20]), 2)
    print(e)
