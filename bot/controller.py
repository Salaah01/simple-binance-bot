"""Main controller that will maintain the connection, and send buy/sell singals
"""

import sys
import os
import json
import traceback
from datetime import datetime
import numpy as np
import websocket
from strategies import rsi, bollinger


class Controller:
    def __init__(self, tradeSym: None):

        self.closes = []
        self.ownCoins = False
        self._config = self._set_config(tradeSym)
        self._logger = self._set_logger()
        self._errLogger = self._set_error_logger()

    @staticmethod
    def _set_config(tradeSym) -> dict:
        """Sets the config."""
        with open('config.json') as configFile:
            config = json.load(configFile)

        defaults = config['defaults']

        if tradeSym:
            defaults['trade_symbol'] = tradeSym.upper()
        else:
            tradeSym = defaults['trade_symbol']

        defaults['socket_address'] = defaults['socket_address'].replace(
            '{{trade_symbol}}',
            tradeSym.lower()
        )

        return config

    @staticmethod
    def timestamp() -> str:
        """Returns a string representation of the current timestamp."""
        return datetime.now().strftime('%Y-%m-%d %H:%M')

    def _set_logger(self):
        """Creates and opens the log."""
        tradeSym = self.get_config()['defaults']['trade_symbol']
        timestamp = self.timestamp().replace(':', '.').replace(' ', '_')

        return open(
            os.path.join('logs', f'{tradeSym}_{timestamp}.log'),
            'a',
            buffering=1
        )

    def _set_error_logger(self):
        """Creates and opens the error log."""
        tradeSym = self.get_config()['defaults']['trade_symbol']
        timestamp = self.timestamp().replace(':', '.').replace(' ', '_')

        return open(
            os.path.join('logs', f'{tradeSym}_{timestamp}.error.log'),
            'a',
            buffering=1
        )

    def log(self, msg: str) -> None:
        """Logs a new entry."""
        self._logger.write(f'{self.timestamp()}\t{msg}\n')

    def log_error(self, msg: str) -> None:
        """Logs an error message."""
        print(msg)
        self._errLogger.write(f'{self.timestamp()}\t{msg}\n')

    @staticmethod
    def on_open(ws):
        """Method to run when the socket is opened."""
        print('connection opened.')

    @staticmethod
    def on_close(ws):
        """Method to run when the socket is closed."""
        print('connection closed.')

    def on_message(self, ws, message):
        """Action to perform whenever a new message is received."""

        try:
            msg = json.loads(message)
            candle = msg['k']

            if not candle['x']:
                return
            
            close = candle['c']
            
            
            self.log(f'CONTROLLER: CLOSED AT {close}')
            print(
                f'{self.get_config()["defaults"]["trade_symbol"]} CLOSED AT: {close}'
            )
            self.closes.append(float(close))

            closes = np.array(self.closes)

            # RSI Strategy
            rsiStrat = self.get_config()['strategies']['rsi']
            rsiResult = rsi(
                closes,
                rsiStrat['period'],
                rsiStrat['overbought'],
                rsiStrat['oversold'],
                self.ownCoins,
                self.log
            )

            # Bollinger Strategy
            bollStrat = self.get_config()['strategies']['bollinger']
            bollResult = bollinger(
                closes,
                bollStrat['period'],
                bollStrat['nbdevup'],
                bollStrat['nbdevdn'],
                bollStrat['matype'],
                self.ownCoins,
                self.log
            )

            # Execute buy/sell order
            if rsiResult == 1 and bollResult == 1:
                self.log('CONTROLLER: BUY')
                self.ownCoins = True
            elif rsiResult == -1 and bollResult == -1:
                self.log('CONTROLLER: SELL')
                self.ownCoins = False

        except Exception:
            self.log_error(traceback.format_exc())

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
    if len(sys.argv) == 2:
        Controller(sys.argv[1]).run()
    else:
        Controller(sys.argv[1]).run()
