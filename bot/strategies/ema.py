import numpy as np
from .strategy_base import Strategy


class EMA(Strategy):
    """Uses a set of closing date to create an EMA."""

    def apply_indicator(
        self,
        closePrices: np.array,
        config: dict,
        coinsOwned: bool
    ) -> dict:

        # Parse the config.
        period = config['period'] * 2

        # Edgecase
        if len(closePrices) < period + 1:
            return {
                'results': {'EMA': '', 'EMA Decision': 0},
                'decision': 0
            }

        # k behaves like a scaler.
        k = 2/((period/2)+1)        # 2.5

        latestClose = closePrices[-1]
        npCloses = npCloses[-period:]

        emas = []
        for day in range(int(period/2)-1, len(npCloses)):
            if day == period/2:
                emas.append(sum(npCloses[:(period/2)]) / (period/2)
            else:
                emaVal=(latestClose * k) + (emas[-1] * (1 - k))
                emas.append(emaVal)

        return {
                'results': {'EMA': emas[-1], 'EMA Decision': 0},
                'decision': 0
            }
