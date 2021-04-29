"""Main controller that will maintain the connection, and send buy/sell singals
"""

import os
import json
import pprint
from datetime import datetime
import numpy as np
import websocket
import talib
from strategies import rsi


class Controller:
    def __init__(self):

        self.closes = []
        self.ownCoins = False
        self._config = self._set_config()
        self._logger = self._set_logger()

    @staticmethod
    def _set_config() -> dict:
        """Sets the config."""
        with open('config.json') as configFile:
            return json.load(configFile)

    @staticmethod
    def timestamp() -> str:
        """Returns a string representation of the current timestamp."""
        return datetime.now().strftime('%Y-%m-%d-%H%M')

    def _set_logger(self):
        """Creates and opens the log."""

        return open(
            os.path.join(
                'logs',
                f'{self.get_config()["defaults"]["trade_symbol"]}{self.timestamp()}.log',
            ),
            'a',
            buffering=1
        )

    def log(self, msg: str) -> None:
        """Logs a new entry."""
        self._logger.write(f'{self.timestamp()}\t{msg}\n')

    @staticmethod
    def on_open(ws):
        """Method to run when the socket is opened."""
        print('connection opened.')

    @staticmethod
    def on_close(ws):
        """Method to run when the socket is closed."""
        print('connection closed.')
        self._logger.close()

    def on_message(self, ws, message):
        """Action to perform whenever a new message is received."""

        msg = json.loads(message)
        candle = msg['k']
        pprint.pprint(msg)

        if not candle['x']:
            return
        close = candle['c']
        self.log(f'CLOSED AT: {close}')
        self.closes.append(float(close))

        closes = np.array(self.closes)

        # RSI Strategy
        rsiStrat = self.get_config()['strategies']['rsi']
        rsi(
            closes,
            rsiStrat['period'],
            rsiStrat['overbought'],
            rsiStrat['oversold'],
            self.ownCoins,
            self.log
        )

        if len(self.closes) < rsiStrat['period']:
            return

        # rsi = talib.RSI(np.array(self.closes), rsiStrat['period'])
        # lastRSI = rsi[-1]
        # self.log(f'RSI: {lastRSI}')

        # if lastRSI >= rsiStrat['overbought'] and self.ownCoins:
        #     self.log('sell')
        #     self.ownCoins = False

        # elif lastRSI <= rsiStrat['oversold'] and not self.ownCoins:
        #     self.log('buy')
        #     self.ownCoins = True

    def run(self):
        ws = websocket.WebSocketApp(
            self.get_config()['defaults']['socket_address'],
            on_open=self.on_open,
            on_close=self.on_close,
            on_message=self.on_message
        )
        ws.run_forever()

    def get_config(self) -> dict:
        """Returns the config."""
        return self._config


if __name__ == '__main__':
    Controller().run()
