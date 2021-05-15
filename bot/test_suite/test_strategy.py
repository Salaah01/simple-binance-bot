"""Tests strategies."""

import sys
import os
ROOT = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
sys.path.append(ROOT)

import json
from typing import List, Optional
from collections import namedtuple
from datetime import datetime
import numpy as np
from etaprogress.progress import ProgressBar
from strategies import RSI, Bollinger
from db_connection import connection

# Set the base config.
with open(os.path.join(ROOT, 'config.json')) as configFile:
    CONFIG = json.load(configFile)   
  

class TestStrategy:
    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        config: dict = CONFIG
    ):

        self.config = config
        self.conn = connection()
        self.cur = self.conn.cursor()

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

        keys = ['openTime', 'symbol', 'openPrice', 'highprice', 'lowPrice',
                'closePrice', 'volume', 'closeTime', 'quoteAssetVolume',
                'noTraders', 'takerBuyBaseAssetVol', 'takeBuyQuoteAssetVol']
        
        results = self.cur.fetchall()
        return namedtuple(
            'loadedData',
            ['data', 'count']
        )((dict(zip(keys, result)) for result in results), len(results))

    def test_strategies(self, strategies:List, symbol: str):
        """Test a list of strategies."""

        closes = []
        wins = []
        losses = []

        pnl = 100
        startPnl = pnl
        buyPrice = 10
        purchasePrice = 0

        loadedData = self.load_data(symbol)
        ownCoin =  False

        outputFile = open(
            f"test_results_{datetime.now().strftime('%Y-%m-%d %H.%M')}_{symbol}.csv",
            'w+',
        )

        progressBar = ProgressBar(loadedData.count)

        writeHeaders = True

        for idx, data in enumerate(loadedData.data):
            results = []

            closes.append(data['closePrice'])
            
            for strategy in strategies:
                config = self.config['strategies'][strategy.__name__.lower()]
                
                result = strategy(lambda _: None).apply_indicator(
                    np.array(closes),
                    config,
                    ownCoin
                )
                results.append(result)

            decisions = [result['decision'] for result in results]
            if all(decision == 1 for decision in decisions):
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

                if priceDiff >= 0:
                    wins.append(priceDiff)
                else:
                    losses.append(priceDiff)
            
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

        # Averages
        winsRatio = round(len(wins)/(len(wins) + len(losses)) * 100, 2)
        winsAvg = round(sum(wins) / (len(wwwwins) or 1) * 100, 2)
        lossesAvg = round(sum(losses) / (len(losses) or 1) * 100, 2)
        pnlChange = round(pnl - startPnl, 2)
        totalTrades = (len(wins) + len(losses)) / 2
        gainPerTrade = round(pnlChange / totalTrades, 2)

        print(f'TOTAL TRADES      : {(len(wins) + len(losses)) / 2}')
        print(f'STARTING PNL      : {startPnl}')
        print(f'END PNL           : {round(pnl, 2)}')
        print(f'PNL CHANGE        : {pnlChange}')
        print(f'GAINS PER TRADE   : {gainPerTrade}')
        print(f'PNL WIN/LOSS      : {round((pnlChange)/startPnl * 100, 2)}%')
        print(f'WIN RATIO         : {winsRatio}%')
        print(f'WIN AVERAGE GAIN  : {winsAvg}%')
        print(f'LOSS AVERAGE GAIN : {lossesAvg}%')

if __name__ == '__main__':
    TestStrategy().test_strategies([RSI, Bollinger], 'BTCGBP')
    # TestStrategy().test_strategies([RSI, Bollinger], 'BNBUSDT')
