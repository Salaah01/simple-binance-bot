from .strategy_base import Strategy
from .ema import EMA


class EMABuy100(Strategy):

    def apply_indicator(self, closePrices, config, coinsOwned):

        period = 100
        if len(closePrices) <= period:
            return {
                'results': {
                    'EMA Value': '',
                    'Decision': 0
                },
                'decision': 0
            }

        if not coinsOwned:
            emaVal = EMA().calc_ema(closePrices, period)
            decision = 1 if emaVal.iloc[-1] >= closePrices[-1] else 0
            self.log(f'EMA: {emaVal.iloc[-1]}')
            return {
                'results': {
                    'EMA Value': emaVal.iloc[-1],
                    'Decision': decision
                },
                'decision': decision
            }

        else:
            return {
                'results': {
                    'EMA Value': '',
                    'Decision': -1,
                },
                'decision': -1
            }
