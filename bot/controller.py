"""Main controller that will maintain the connection, and send buy/sell
singals
"""

import os
import json
import traceback
from datetime import datetime
import numpy as np
import websocket
from send_order_signal import SendOrderSignal
from binance.enums import SIDE_BUY, SIDE_SELL
from strategies import rsi, bollinger
from args_parser import args_parser


class Controller:
    def __init__(self, options):
        """Main controller that will maintain the connection, and send buy/sell
        singals.

        Args:
            options - (namespace) Collection of configuration options.
        """
        self.closes = []
        self.purchasedPrice = 0
        self.ownCoins = options.coin_owned

        self._config = self._set_config(options)

        # Set common config options to the self object for easy referencing.
        self._testMode = self.get_config()['testing']['testing']
        self._tradeSym = self.get_config()['defaults']['trade_symbol']
        self._asset = self.get_config()['defaults']['asset']

        # Caluclate stop loss multiplier.
        self._stopLoss = self.get_config()['defaults']['stop_loss_percent']
        self._stopLoss = (100 - float(self._stopLoss)) / 100

        if not self._testMode:
            self._postRequests = True
        else:
            self._postRequests = self.get_config()['testing']['post_requests']

        # Create loggers.
        self._logger = self._set_logger()
        self._errLogger = self._set_error_logger()
        self._outputDataset = self._set_output_dataset()

        self._signalDispatcher = None

    @staticmethod
    def _set_config(options) -> dict:
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

        # Update default values frm the args.
        defaults['trade_symbol'] = options.trade_symbol.upper()
        defaults['asset'] = options.asset

        defaults['socket_address'] = defaults['socket_address']\
            .replace('{{trade_symbol}}', options.trade_symbol.lower())\
            .replace('{{interval}}', defaults['interval'])

        # If buy options have provided in the CLI, then override the options
        # defined in the config.
        buyOpts = config['buy_options']
        if options.buy_mode:
            buyOpts['mode'] = options.buy_mode
        if options.balance_percent:
            buyOpts['balance_percent'] = options.balance_percent
        if options.flat_amount:
            buyOpts['flat_amount'] = options.flat_amount
        if options.balance_percent:
            buyOpts['balance_percent'] = options.balance_percent

        # Update test mode.
        config['testing']['testing'] = options.test_mode

        return config

    @staticmethod
    def timestamp() -> str:
        """Returns a string representation of the current timestamp."""
        return datetime.now().strftime('%Y-%m-%d %H:%M')

    def test_logger(self):
        """A logging object for testing. Instead of writing to a file, it will
        mimic be behaviour, but instead write to stdout.
        """

        class Logger:
            @staticmethod
            def write(msg: str):
                print(msg)

            @staticmethod
            def close():
                pass

        return Logger()

    def _set_logger(self):
        """Creates and opens the log."""
        if self._testMode:
            return self.test_logger()

        timestamp = self.timestamp().replace(':', '.').replace(' ', '_')

        return open(
            os.path.join('logs', f'{self._tradeSym}_{timestamp}.log'),
            'a',
            buffering=1
        )

    def _set_error_logger(self):
        """Creates and opens the error log."""
        if self._testMode:
            return self.test_logger()

        timestamp = self.timestamp().replace(':', '.').replace(' ', '_')

        return open(
            os.path.join('logs', f'{self._tradeSym}_{timestamp}.error.log'),
            'a',
            buffering=1
        )

    def _set_output_dataset(self):
        """Creates and opens the log."""
        if self._testMode:
            return self.test_logger()

        timestamp = self.timestamp().replace(':', '.').replace(' ', '_')

        dataset = open(
            os.path.join('logs', f'{self._tradeSym}_{timestamp}_dataset.csv'),
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
        self._errLogger.close()
        self._outputDataset.close()
        print('connection closed.')

    def buy_quantity(self, closePrice: float) -> float:
        """Calculates the buy quantity taking in consideration the price for
        each coin and the buy strategy defined in the config.

        Args:
            closePrice - (float) The closing price of the coin.

        Returns:
            float - Quantity to buy.
        """
        buyOpts = self.get_config()['buy_options']

        # If user choices a flat balance, then device the balance by the
        # # closing price.
        if buyOpts['mode'] == 'balance_amount':
            quantity = buyOpts['flat_amount'] / float(closePrice)

        # If user choices a balance percentage, fetch their balance, update the
        # balance to invest by multiplying by the chosen percentage and then
        # devide by the closing price.
        elif buyOpts['mode'] == 'balance_percent':
            balance = self._signalDispatcher.asset_balance(self._asset)
            quantity = balance * buyOpts['balance_percent'] / 100 / closePrice

        return self._signalDispatcher.apply_filters(
            self._tradeSym,
            quantity
        )

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

            close = float(candle['c'])

            self.log(f'CONTROLLER: CLOSED AT {close}')
            print(f'{self._tradeSym} CLOSED AT: {close}')

            self.closes.append(close)

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
            # Execute buy/sell order
            if rsiResult.decision == 1 and bollResult.decision == 1:
                self.log('CONTROLLER: BUY')
                print('\033[92mBUY\033[0m')

                if self._postRequests:
                    res = self._signalDispatcher.send_signal(
                        SIDE_BUY,
                        self._tradeSym.upper(),
                        self.buy_quantity(close),
                        self._testMode
                    )

                    # Send buys signal.
                    if res['success']:
                        self.ownCoins = True
                        self.purchasedPrice = close

                        self.log('SIGNAL: BOUGHT')
                        print('\033[92mSIGNAL BOUGHT.\033[0m')

                    else:
                        self.ownCoins = False
                        self.purchasedPrice = 0

                        self.log('SIGNAL: ERROR BUYING')
                        self.log_error(res['error'])
                        self.log_error(res['params'])

                else:
                    # The post request mode would equal False during testing,
                    # so assume that the request has gone through.
                    self.ownCoins = True
                    self.purchasedPrice = close

            elif rsiResult.decision == -1 and bollResult.decision == -1:
                # Get and sell the entire stock.

                self.log('CONTROLLER: SELL')

                if self._postRequests:
                    quantity = self._signalDispatcher.apply_filters(
                        self._tradeSym,
                        self._signalDispatcher.asset_balance(
                            self._tradeSym.replace(self._asset.upper(), '')
                        )
                    )

                    print(f'\033[92mSELLING {quantity}\033[0m')

                    res = self._signalDispatcher.send_signal(
                        SIDE_SELL,
                        self._tradeSym.upper(),
                        quantity,
                        self._testMode
                    )

                    # Send sell signal
                    if res['success']:
                        self.ownCoins = False
                        self.purchasedPrice = 0
                        self.log('SIGNAL: SOLD')
                        print('\033[92mSIGNAL SOLD.\033[0m')

                    else:
                        self.ownCoins = True
                        self.log('SIGNAL: ERROR SELLING')
                        self.log_error(res['error'])
                        self.log_error(res['params'])

                else:
                    # The post request mode would equal False during testing,
                    # so assume that the request has gone through.
                    self.ownCoins = False
                    self.purchasedPrice = 0

            # Stop loss
            elif (self.purchasedPrice
                    and close <= self.purchasedPrice * self._stopLoss):
                print('\033[92mSELLING TO PREVENT STOP LOSS.\033[0m')

                if self._postRequests:
                    quantity = self._signalDispatcher.apply_filters(
                        self._tradeSym,
                        self._signalDispatcher.asset_balance(
                            self._tradeSym.replace(self._asset.upper(), '')
                        )
                    )
                    print(f'\033[92mSELLING {quantity}\033[0m')

                    res = self._signalDispatcher.send_signal(
                        SIDE_SELL,
                        self._tradeSym.upper(),
                        quantity,
                        self._testMode
                    )

                    # Send sell signal
                    if res['success']:
                        self.ownCoins = False
                        self.purchasedPrice = 0
                        self.log('SIGNAL: SOLD')
                        print('\033[92mSIGNAL SOLD.\033[0m')

                    else:
                        self.ownCoins = True
                        self.log('SIGNAL: ERROR SELLING')
                        self.log_error(res['error'])
                        self.log_error(res['params'])

                else:
                    # The post request mode would equal False during testing,
                    # so assume that the request has gone through.
                    self.ownCoins = False
                    self.purchasedPrice = 0

            # Update the dataset.
            dataset = [close, rsiResult.rsi, rsiResult.decision,
                       bollResult.high, bollResult.low, bollResult.decision]
            dataset = [str(data) for data in dataset]
            self.add_dataset('|'.join(dataset))

        except Exception:
            err = traceback.format_exc()
            self.log_error(err)
            print(f'\033[92m{err}\033[0m')

    def run(self):
        """Runs the trading process."""
        self._signalDispatcher = SendOrderSignal()
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


def main():
    Controller(args_parser()).run()


if __name__ == '__main__':
    main()
