"""Tests trading strategies."""
from time import time
import sys
import os
ROOT = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
sys.path.append(ROOT)
import traceback  # noqa E402
import json  # noqa E402
from typing import List, Optional  # noqa E402
from collections import namedtuple  # noqa E402
from datetime import datetime  # noqa E402
import numpy as np  # noqa E402
from etaprogress.progress import ProgressBar  # noqa E402
from strategies import RSI, Bollinger, KeltnerChannels  # noqa E402
from db_connection import connection  # noqa E402

# Set the base config.
with open(os.path.join(ROOT, 'config.json')) as configFile:
    CONFIG = json.load(configFile)


class TestStrategy:
    """Tests trading strategies."""

    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        config: dict = CONFIG
    ) -> None:
        """Fetches symbols and sets variables to the `self` object."""

        self.config = config
        self.conn = connection()
        self.cur = self.conn.cursor()

        # If no symbols have been provided, assume that the request is to
        # test through all symbols.
        if symbols is None:
            self.symbols = self.load_symbols()
        else:
            self.symbols = symbols

    def load_symbols(self) -> list:
        """Loads all the symbols."""
        self.cur.execute('SELECT * FROM symbols')
        return [symbol[0] for symbol in self.cur.fetchall()]

    def load_data(self, symbol: str):
        """Loads the data for a given `symbol`.

        Args:
            symbol - (str) Trade symbol.

        Returns
            Generator for a list of dictionaries containing data from the
                database.
        """

        self.cur.execute(
            """SELECT open_time, symbol, open_price, high_price, low_price,
                      close_price, volume, close_time, quote_asset_volume,
                      no_traders, taker_buy_base_asset_vol,
                      taker_buy_quote_asset_vol
            FROM prices WHERE symbol = %s
            ORDER BY open_time
            """,
            (symbol,)
        )

        keys = ['openTime', 'symbol', 'openPrice', 'highPrice', 'lowPrice',
                'closePrice', 'volume', 'closeTime', 'quoteAssetVolume',
                'noTraders', 'takerBuyBaseAssetVol', 'takeBuyQuoteAssetVol']

        results = self.cur.fetchall()
        return namedtuple(
            'loadedData',
            ['data', 'count']
        )((dict(zip(keys, result)) for result in results), len(results))

    def test_strategies(
        self,
        strategies: List,
        symbol: str,
        stopLoss: bool = False,
        buyAfterSL: bool = False,
    ) -> None:
        """Test a list of strategies. Writes results into a file and prints a
        summary of the test results.

        Args:
            strategies - (List) collection of strategies.
            symbol - (str) Trade symbol.
            stopLoss - (bool) Should the stop loss be used?
            buyAfterSL - (bool) Force a purchase once the prices drop seems to
                flatten after a stop loss.
        Returns:
            None
        """
        startTime = time()

        # Prices
        closes = []
        lows = []
        highs = []

        # Collects wins and losses.
        wins = []
        losses = []

        stopLossCount = 0

        # Params
        pnl = 100
        startPnl = pnl
        buyPrice = 10
        purchasePrice = 0
        inStopLoss = False

        loadedData = self.load_data(symbol)
        ownCoin = False

        stratNames = ','.join([strategy.__name__ for strategy in strategies])

        outputFileName = os.path.join(
            'results',
            f"test_results_{datetime.now().strftime('%Y-%m-%d %H.%M')} {symbol} {stratNames}"  # noqa: E501
        )
        outputFile = open(f'{outputFileName}.csv', 'w+')
        resultsFile = open(f'{outputFileName}.txt', 'w+')

        progressBar = ProgressBar(loadedData.count)
        writeHeaders = True

        # In the config, certain strategies require additional arguments.
        # These strategies will use the following argument map to fetch the
        # correct variable.
        argsMap = {
            'keltnerchannels': {
                '_lowPrices': lambda: lows,
                '_highPrices': lambda: highs
            }
        }

        npArraySize = -self.config['defaults']['closes_array_size']

        for idx, data in enumerate(loadedData.data):
            try:
                results = []

                closes.append(data['closePrice'])
                lows.append(data['lowPrice'])
                highs.append(data['highPrice'])

                for strategy in strategies:
                    className = strategy.__name__.lower()
                    config = self.config['strategies'][className]

                    result = strategy(lambda _: None).apply_indicator(
                        np.array(closes[-npArraySize:]),
                        config,
                        ownCoin,
                        *[argsMap[className][arg]()[-npArraySize:]
                          for arg in config.get('additional_args', [])]
                    )
                    results.append(result)

                decisions = [result['decision'] for result in results]
                if (all(decision == 1 for decision in decisions)
                        and not inStopLoss):
                    ownCoin = True
                    unitsOwned = buyPrice / data['closePrice']
                    pnl -= buyPrice
                    purchasePrice = data['closePrice']

                elif all(decision == -1 for decision in decisions):
                    ownCoin = False
                    pnl += data['closePrice'] * unitsOwned
                    unitsOwned = 0

                    priceDiff = ((data['closePrice'] - purchasePrice)
                                 / purchasePrice)

                    purchasePrice = 0

                    if priceDiff >= 0:
                        wins.append(priceDiff)
                    else:
                        losses.append(priceDiff)

                elif (stopLoss
                      and ownCoin
                      and self.stopLoss(purchasePrice, data['closePrice'])):

                    ownCoin = False
                    pnl += data['closePrice'] * unitsOwned
                    unitsOwned = 0

                    priceDiff = ((data['closePrice'] - purchasePrice)
                                 / purchasePrice)

                    purchasePrice = 0
                    losses.append(priceDiff)
                    stopLossCount += 1
                    inStopLoss = True

                elif inStopLoss and data['closePrice'] >= closes[-2]:
                    inStopLoss = False

                    # Force a buy after the stop loss period.
                    if buyAfterSL:
                        ownCoin = True
                        unitsOwned = buyPrice / data['closePrice']
                        pnl -= buyPrice
                        purchasePrice = data['closePrice']

                # Write the results to a csv.
                if writeHeaders:
                    headers = ['Open Time', 'Close Price', 'PnL']
                    for res in results:
                        headers += list(res['results'].keys())

                    outputFile.write(f"{'|'.join(headers)}\n")
                    writeHeaders = False

                resultVals = [str(data['openTime']), str(data['closePrice']),
                              str(pnl)]

                for res in results:
                    resultVals += [str(r) for r in res['results'].values()]
                outputFile.write(f"{'|'.join(resultVals)}\n")

                # Update progress
                if not idx % 100 or idx == loadedData.count:
                    progressBar.numerator = idx
                    print(progressBar, end='\r')

            except Exception:
                print(traceback.format_exc())

        # Results
        mins, secs = divmod(time() - startTime, 60)
        winsRatio = round(len(wins)/(len(wins) + len(losses)) * 100, 2)
        winsAvg = round(sum(wins) / (len(wins) or 1) * 100, 2)
        lossesAvg = round(sum(losses) / (len(losses) or 1) * 100, 2)
        pnlChange = round(pnl - startPnl, 2)
        totalTrades = (len(wins) + len(losses)) / 2
        gainPerTrade = round(pnlChange / totalTrades, 2)

        resultsOutputs = [
            f'TIME              : {int(mins)}mins {int(secs)}secs',
            f'STOP LOSS COUNT   : {stopLossCount}',
            f'TOTAL TRADES      : {(len(wins) + len(losses)) / 2}',
            f'STARTING PNL      : {startPnl}',
            f'END PNL           : {round(pnl, 2)}',
            f'PNL CHANGE        : {pnlChange}',
            f'% PNL CHANGE      : {round((pnlChange)/startPnl * 100, 2)}%',
            f'GAINS PER TRADE   : {gainPerTrade}',
            f'% GAIN PER TRADE  : {round(gainPerTrade / startPnl * 100, 2)}',
            f'WIN RATIO         : {winsRatio}%',
            f'WIN AVERAGE GAIN  : {winsAvg}%',
            f'LOSS AVERAGE GAIN : {lossesAvg}%'
        ]

        print()
        for resultOutput in resultsOutputs:
            print(resultOutput)
            resultsFile.write(f'{resultOutput}\n')
        resultsFile.write(json.dumps(self.config))

        outputFile.close()
        resultsFile.close()

    def stopLoss(self, purchasePrice, closePrice) -> bool:
        multiplier = (100 - self.config['defaults']['stop_loss_percent']) / 100
        return closePrice <= purchasePrice * multiplier


if __name__ == '__main__':
    # TestStrategy().test_strategies([KeltnerChannels], 'BTCGBP', True, True)
    TestStrategy().test_strategies([RSI, Bollinger], 'BTCGBP', True, True)
    # TestStrategy().test_strategies([RSI, Bollinger], 'BNBUSDT')
