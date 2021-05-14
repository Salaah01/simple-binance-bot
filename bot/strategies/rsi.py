from typing import Callable, Optional
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
        if len(npCloses) <= period:
            return {
                'results': {'RSI Value': '', 'RSI Decision': 0},
                'decision': 0
            }

        gains = []
        loses = []
        avgGains = []
        avgLosses = []
        relativeStrength = []
        relativeStrengthIndex = []

        if len(npCloses) >= 3 * period:
            npCloses = npCloses[-(3*period):]

        for c in range(1, len(npCloses)):
            # Check gains / loses
            if npCloses[c] >= npCloses[c-1]:
                gains.append(npCloses[c] - npCloses[c-1])
                loses.append(0)
            else:
                loses.append(npCloses[c-1] - npCloses[c])
                gains.append(0)

            # Check average gains / loses
            if c == period:
                avgGains.append(sum(gains) / period)
                avgLosses.append(sum(loses) / period)
            elif c > period:
                avgGains.append(((avgGains[-1]*(period-1)+gains[-1])/period))
                avgLosses.append(((avgLosses[-1]*(period-1)+loses[-1])/period))

            # Calculates RS and RSI value
            if c >= period:
                relativeStrength.append(avgGains[-1]/avgLosses[-1])
                relativeStrengthIndex.append(
                    100 - (100 / (relativeStrength[-1] + 1)))

        rsiValue = relativeStrengthIndex[-1]
        self.log(f'RSI: {rsiValue}')

        if rsiValue >= overboughtLimit and coinsOwned:
            self.log('RSI: SELL')
            decision = -1
        elif rsiValue <= oversoldLimit and not coinsOwned:
            self.log('RSI: BUY')
            decision = 1
        else:
            decision = 0

        return {
            'results': {'RSI Value': rsiValue, 'RSI Decision': decision},
            'decision': decision
        }

    @staticmethod
    def calc_rsi(npCloses: np.array, period: int) -> float: