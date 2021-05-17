from collections import namedtuple
import numpy as np
import pandas as pd
try:
    from .strategy_base import Strategy
except ImportError:
    from strategy_base import Strategy


class StochRSI(Strategy):
    """Applies the Stochastic RSI onto a collection of closing prices."""

    def apply_indicator(
        self,
        closePrices: np.array,
        config: dict,
        coinsOwned: bool
    ) -> dict:

        period = config['period']
        overboughtLimit = config['overbought_limit']
        oversoldLimit = config['oversold_limit']

        # Edgecase to prevent innacuracy of results and preventing the usage
        # of sma over ema 
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


if __name__ == "__main__":
    # import pandas as pd
    data = pd.Series([25.89600, 25.88000, 25.92100, 25.92100, 25.86000, 26.00500, 26.00500, 26.01600, 26.00300, 26.04000, 26.05700, 26.12800,
                      26.11400, 26.11400, 26.03900, 26.091, 26.054, 26.002, 25.854, 25.866, 25.858, 26.009, 25.91, 25.885, 25.908, 25.893, 25.893, 25.911, 25.903])
    config = {
        "period": 14,
        "overbought_limit": 80,
        "oversold_limit": 20
    }
    coinsOwned = True
    stochrsi = StochRSI().apply_indicator(data, config, coinsOwned)
    print(stochrsi)

