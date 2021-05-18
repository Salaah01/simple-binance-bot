from .strategy_base import Strategy
from .ema import EMA


class EMABuy50And100(Strategy):

    def apply_indicator(self, closePrices, config, coinsOwned):

        period = 100
        if len(closePrices) <= period:
            return {
                'results': {
                    'EMA 50': '',
                    'EMA 100': '',
                    'Decision': 0
                },
                'decision': 0
            }

        if not coinsOwned:
            ema100 = EMA().calc_ema(closePrices, period)
            ema50 = EMA().calc_ema(closePrices, 50)
            
            # decision = 1 if emaVal.iloc[-1] >= closePrices[-1] else 0
            decision = 1 if ema50.iloc[-1] >= ema100.iloc[-1] else 0
            self.log(f'EMA 50: {ema50.iloc[-1]}, EMA 100: {ema100.iloc[-1]}')
            return {
                'results': {
                    'EMA 50': ema50.iloc[-1],
                    'EMA 100': ema100.iloc[-1],
                    'Decision': decision
                },
                'decision': decision
            }

        else:
            return {
                'results': {
                    'EMA 50': '',
                    'EMA 100': '',
                    'Decision': -1,
                },
                'decision': -1
            }
