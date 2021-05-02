"""Main controller that will maintain the connection, and send buy/sell
singals
"""

from typing import Optional
import sys
import os
import json
import traceback
from datetime import datetime
import numpy as np
import websocket
from strategies import rsi, bollinger
from send_order_signal import SendOrderSignal
from binance.enums import SIDE_BUY, SIDE_SELL


class Controller:
    def __init__(
        self,
        tradeSym: Optional[str] = None,
        asset: Optional[str] = None
    ):
        """Main controller that will maintain the connection, and send buy/sell
        singals.

        Args:
            tradeSym - (str) Trade symbol (pair) to trade in.
            asset - (str) Asset name to trade in.
        """
        self.closes = []
        self.ownCoins = False

        self._config = self._set_config(tradeSym, asset)
        self._logger = self._set_logger()
        self._errLogger = self._set_error_logger()
        self._outputDataset = self._set_output_dataset()

        self.signalDispatcher = SendOrderSignal()

    @staticmethod
    def _set_config(
        tradeSym: Optional[str] = None,
        asset: Optional[str] = None
    ) -> dict:
        """Sets the config.

        Args:
            tradeSym - (str) Trade symbol (pair) to trade in.
            asset - (str) Asset name to trade in.

        Returns:
            dict - Configuration.
        """

        # Parse config.
        with open('config.json') as configFile:
            config = json.load(configFile)

        defaults = config['defaults']

        # Update default values if provided.
        if tradeSym:
            defaults['trade_symbol'] = tradeSym.upper()
        else:
            tradeSym = defaults['trade_symbol']

        if asset:
            defaults['asset'] = asset

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

    def _set_output_dataset(self):
        """Creates and opens the log."""
        tradeSym = self.get_config()['defaults']['trade_symbol']
        timestamp = self.timestamp().replace(':', '.').replace(' ', '_')

        dataset = open(
            os.path.join('logs', f'{tradeSym}_{timestamp}_dataset.csv'),
            'a',
            buffering=1
        )
        columnHeadings = ['Timestamp', 'Close', 'RSI Value', 'RSI Decision',
                          'Bollinger High', 'Bollinger Low',
                          'Bollinger Decision']
        dataset.write(f"{'|'.join(columnHeadings)}\n")
        return dataset

    def log(self, msg: str) -> None:
        """Logs a new entry.

        Args:
            msg - (str) Message to log.
        """
        self._logger.write(f'{self.timestamp()}\t{msg}\n')

    def log_error(self, msg: str) -> None:
        """Logs an error message.

        Args:
            msg - (str) Message to log.
        """
        print(msg)
        self._errLogger.write(f'{self.timestamp()}\t{msg}\n')

    def add_dataset(self, msg) -> None:
        """Adds to the dataset."""
        self._outputDataset.write(f'{self.timestamp()}|{msg}\n')

    @staticmethod
    def on_open(ws: websocket.WebSocketApp):
        """Method to run when the socket is opened.

        Args:
            ws - (websocket.WebSocketApp) Websocket object.
        """
        print('connection opened.')

    def on_close(self, ws: websocket.WebSocketApp):
        """Method to run when the socket is closed.

         Args:
            ws - (websocket.WebSocketApp) Websocket object.
        """
        self._logger.close()
        print('connection closed.')

    def on_message(self, ws: websocket.WebSocketApp, message: json) -> None:
        """Action to perform whenever a new message is received.

         Args:
            ws - (websocket.WebSocketApp) Websocket object.
            message - (json) Message returned from websocket.
        """

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
                self.ownCoins,
                self.log
            )

            # ###################################################################
            # quantity = round(
            #     self.get_config()['defaults']['amount'] / float(close),
            #     6
            # )
            # self.log(f'quantity 1: {quantity}')

            # tradeSym = self.get_config(
            # )['defaults']['trade_symbol'].upper()
            # quantity = self.signalDispatcher.apply_filters(
            #     tradeSym,
            #     quantity
            # )
            # self.log(f'quantity 2: {quantity}')
            # ###################################################################

            # Execute buy/sell order
            if rsiResult.decision == 1 and bollResult.decision == 1:
                self.log('CONTROLLER: BUY')
                print('\033[92mBUY\033[0m')

                quantity = round(
                    self.get_config()['defaults']['amount'] / float(close),
                    6
                )

                self.log(f'CONTROLLER: SENDING {quantity} (quantity) to func.')
                print(
                    f'\033[94mCONTROLLER: SENDING {quantity} (quantity) to func.\033[0m')

                quantity = self.signalDispatcher.apply_filters(
                    self.get_config()['defaults']['trade_symbol'].upper(),
                    quantity
                )

                self.log(f'Buying {quantity}')

                res = self.signalDispatcher.send_signal(
                    SIDE_BUY,
                    self.get_config()['defaults']['trade_symbol'].upper(),
                    quantity
                )

                # Send buys signal.
                if res['success']:
                    self.ownCoins = True
                    self.log('SIGNAL: BOUGHT')
                    print('\033[92mSIGNAL BOUGHT.\033[0m')
                else:
                    self.ownCoins = False
                    self.log('SIGNAL: ERROR BUYING')
                    self.log_error(res['error'])

            elif rsiResult.decision == -1 and bollResult.decision == -1:
                self.log('CONTROLLER: SELL')
                print('\033[92mSELL\033[0m')

                quantity = self.signalDispatcher.apply_filters(
                    self.get_config()['defaults']['trade_symbol'].upper(),
                    self.signalDispatcher.asset_balance(
                        self.get_config()['defaults']['asset']
                    )
                )

                res = self.signalDispatcher.send_signal(
                    SIDE_SELL,
                    self.get_config()['defaults']['trade_symbol'].upper(),
                    quantity
                )

                # Send sell signal
                if res['success']:
                    self.ownCoins = False
                    self.log('SIGNAL: SOLD')
                    print('\033[92mSIGNAL SOLD.\033[0m')
                else:
                    self.ownCoins = True
                    self.log('SIGNAL: ERROR SELLING')
                    self.log_error(res['error'])

            # Update the dataset.
            dataset = [float(close), rsiResult.rsi, rsiResult.decision,
                       bollResult.high, bollResult.low, bollResult.decision]
            dataset = [str(data) for data in dataset]
            self.add_dataset('|'.join(dataset))

        except Exception:
            err = traceback.format_exc()
            self.log_error(err)
            print(f'\033[92m{err}\033[0m')

    def run(self):
        """Runs the trading process."""
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
    if len(sys.argv) == 3:
        Controller(sys.argv[1], sys.argv[2]).run()
    else:
        Controller().run()
