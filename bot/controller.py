"""Main controller that will maintain the connection, and send buy/sell
singals
"""

import os
import json
import traceback
from copy import deepcopy
from datetime import datetime
from typing import List
from multiprocessing import Process
import numpy as np
import websocket
from send_order_signal import SendOrderSignal
from trader import Trader
from args_parser import args_parser


def load_config(options) -> dict:
    """Loads the config applying any changes provided by the args parser
    (`options`).

    Args:
        options - (namespace) Collection of configuration options.

    Returns:
        dict - Configurations.
    """
    # Parse config.
    with open('config.json') as configFile:
        config = json.load(configFile)

    defaults = config['defaults']

    defaults['socket_address'] = defaults['socket_address'].replace(
        '{{interval}}',
        defaults['interval']
    )

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

    # Returns a deep copy just in case the dictionary is mutated.
    return deepcopy(config)


class Controller:
    def __init__(self, config: dict, tradeSymbol: str):
        """Main controller that will maintain the connection, and send buy/sell
        singals.

        Args:
            config - (dict) Set of configurations for the class to use.
            tradeSymbol - (str) Trade symbol
        """
        self.config = config
        self.tradeSymbol = tradeSymbol

        self.closes = []
        self._signalDispatcher = None

        # Set common config options to the self object for easy referencing.
        self._testMode = self.config['testing']['testing']
        if not self._testMode:
            self._postRequests = True
        else:
            self._postRequests = self.config['testing']['post_requests']

        # Create loggers
        self._logger = self._set_logger()
        self._errLogger = self._set_error_logger()
        self._outputDataset = self._set_output_dataset()

        # The dataset log is a CSV. The variable below will initialise as
        # `True` as will be set to `False` once the headings has been written
        # to the file.
        self._createDatasetHead = True

    def _set_logger(self):
        """Creates and opens the log."""
        if self._testMode:
            return self.test_logger()

        timestamp = self.timestamp().replace(':', '.').replace(' ', '_')

        return open(
            os.path.join('logs', f'{self.tradeSymbol}_{timestamp}.log'),
            'a',
            buffering=1
        )

    def _set_error_logger(self):
        """Creates and opens the error log."""
        if self._testMode:
            return self.test_logger()

        timestamp = self.timestamp().replace(':', '.').replace(' ', '_')

        return open(
            os.path.join('logs', f'{self.tradeSymbol}_{timestamp}.error.log'),
            'a',
            buffering=1
        )

    def _set_output_dataset(self):
        """Creates and opens the log."""
        if self._testMode:
            return self.test_logger()

        timestamp = self.timestamp().replace(':', '.').replace(' ', '_')

        return open(
            os.path.join('logs', f'{self.tradeSymbol}_{timestamp}_dataset.csv'),
            'a',
            buffering=1
        )

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

    def on_open(self, ws: websocket.WebSocketApp):
        """Method to run when the socket is opened.

        Args:
            ws - (websocket.WebSocketApp) Websocket object.
        """
        print(f'\033[92mConnection to {self.tradeSymbol} opened.\033[0m')

    def on_close(self, ws: websocket.WebSocketApp):
        """Method to run when the socket is closed.

         Args:
            ws - (websocket.WebSocketApp) Websocket object.
        """
        self._logger.close()
        self._errLogger.close()
        self._outputDataset.close()
        print('connection closed.')

    def on_message(self, ws: websocket.WebSocketApp, message: json) -> None:
        """Action to perform whenever a new message is received.

         Args:
            ws - (websocket.WebSocketApp) Websocket object.
            message - (json) Message returned from websocket.
        """
        print(self.tradeSymbol)
        try:
            # Retrieve data from the websocket and progress on once a closing
            # price ha been registered.
            msg = json.loads(message)
            candle = msg['k']

            if not candle['x']:
                return

            close = float(candle['c'])

            self.log(f'CONTROLLER: CLOSED AT {close}')
            print(f'{self.tradeSymbol} CLOSED AT: {close}')

            self.closes.append(close)
            closes = np.array(self.closes)

            # TRADING WILL HAPPEN HERE ========================================

        except Exception:
            err = traceback.format_exc()
            self.log_error(err)
            print(f'\033[92m{err}\033[0m')

    def run(self):
        """Runs the trading process."""
        self._signalDispatcher = SendOrderSignal()
        ws = websocket.WebSocketApp(
            self.config['defaults']['socket_address'].replace(
                '{{trade_symbol}}',
                self.tradeSymbol
            ),
            on_open=self.on_open,
            on_close=self.on_close,
            on_message=self.on_message
        )
        ws.run_forever()


def run_controller(config: dict, tradeSymbol: str):
    Controller(config, tradeSymbol).run()


def main():
    config = load_config(args_parser())

    # processes = []
    # for tradeSymbol in config['trade_symbols']:
    #     process = Process(target=run_controller, args=[config, tradeSymbol])
    #     process.start()
    #     processes.append(process)

    # for process in processes:
    #     process.join()
    run_controller(config, 'ETHGBP')


if __name__ == '__main__':
    main()
