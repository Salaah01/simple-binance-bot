import numpy as np
from .strategy_base import Strategy

class StochRSI(Strategy):
    """Applies the Stochastic RSI onto a collection of closing prices."""

    def apply_indicator(
        self, 
        closePrices:, 
        config, 
        coinsOwned)