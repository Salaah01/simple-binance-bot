"""Applies strategies and sends buy/sell orders for a single coin."""

import os
import json
import traceback
from typing import List
from datetime import datetime
import numpy as np
import websocket
from send_order_signal import SendOrderSignal
from binance.enums import SIDE_BUY, SIDE_SELL
from strategies import RSI, Bollinger


class Trader:
    """Applies strategies and sends buy/sell orders for a single coin."""

    def __init__(
        self,
        tradeSymbol: str,
        config: dict,
        singalDispatcher: SendOrderSignal
    ) -> None:
        """Keeps track of the closing prices and sets certain objects to the
        `self` object for logging and easy referencing.

        Args:
            tradeSymbol - (str) The trade symbol.
            config - (dict) Configurations.
            signalDispatcher - (SendOrderSignal) Instantiated instance of the
                singal dispatcher to be able to communicate with the API.
        """

        self.tradeSymbol = tradeSymbol
        self.config = config
        self.signalDispatcher = singalDispatcher

        # Vars to help keep a track of the state.
        self._closes = []
        self._purchasedPrice = 0

        # Set common config options to the self object for easy referencing.
        self._testMode = self.config['testing']['testing']
        if not self._testMode:
            self._postRequests = True
        else:
            self._postRequests = self.config['testing']['post_requests']

        self._tradeCurrency = self._set_trade_currency()
        self._stopLoss = self._set_stop_loss()

        # Create loggers
        self._logger = self._set_logger()
        self._errLogger = self._set_error_logger()
        self._outputDataset = self._set_output_dataset()

        # The dataset log is a CSV. The variable below will initialise as
        # `True` as will be set to `False` once the headings has been written
        # to the file.
        self._createDatasetHead = True

        self._strategies = [RSI, Bollinger]
        self._ownCoins = self.signalDispatcher.has_coins(
            self._tradeCurrency,
            self.tradeSymbol
        )

    @property
    def closes(self) -> list:
        """Fetches the closing prices."""
        return self._closes

    @closes.setter
    def closes(self, closingPrices: list) -> None:
        """Updates the closing prices.

        Args:
            closingPrices - (list) New closing prices.
        """
        self._closes = closingPrices

    @property
    def purchasedPrice(self) -> float:
        """Fetches the purchased price."""
        return self._purchasedPrice

    @purchasedPrice.setter
    def purchasedPrice(self, price: float) -> None:
        """Updates the purchased price.

        Args:
            price - (float) New purchased price.
        """
        self._purchasedPrice = price

    @property
    def ownCoins(self) -> bool:
        """Are coins currently owned?"""
        return self._ownCoins

    @ownCoins.setter
    def ownCoins(self, owned: bool) -> None:
        """Updates the state of the owned coins.

        Args:
            owned - (bool) Are the coins owned?
        """
        self._ownCoins = owned

    def _set_trade_currency(self) -> str:
        """Sets the asset for the current `tradeSymbol`

        Returns:
            The trade currency for the `tradeSymbol`.
        ."""
        currencies = self.config['trade_currencies']
        for currency in currencies:
            if self.tradeSymbol.endswith(currency):
                return currency
        else:
            raise Exception(
                f'Cannot find the trade currency for {self.tradeSymbol}'
            )

    def get_trade_currency(self) -> str:
        """Fetches the trade currency for the current `tradeSymbol`."""
        return self._tradeCurrency

    def _set_stop_loss(self) -> float:
        """Sets the stop loss multiplier."""
        return (100 - self.config['defaults']['stop_loss_percent']) / 100

    def get_stop_loss(self) -> float:
        """Fetches the stop loss multiplier."""
        return self._stopLoss

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

        return open(
            os.path.join('logs', f'{self._tradeSym}_{timestamp}_dataset.csv'),
            'a',
            buffering=1
        )

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

    def add_closing_price(self, price: float) -> None:
        """Adds a new closing price.

        Args:
            price - (float) Closing price.
        """
        self._closes.append(price)

    def trade(self):
        """Main controller for trading. The method will run the defined
        strategies and make a purchase/sale when relevant and update the log.
        """
        try:
            closes = np.array(self.closes)

            # Run each strategy and collect the results.
            stratResults = self.run_strategies(closes)
            self.action_decision(
                close,
                [stratResult['decision'] for stratResult in stratResults]
            )
            self.stop_loss(close)
            self.update_dataset(stratResults)

        except Exception:
            err = traceback.format_exc()
            self.log_error(err)
            print(f'\033[92m{err}\033[0m')

    def buy_quantity(self, closePrice: float) -> float:
        """Calculates the buy quantity taking in consideration the price for
        each coin and the buy strategy defined in the config.

        Args:
            closePrice - (float) The closing price of the coin.

        Returns:
            float - Quantity to buy.
        """
        buyOpts = self.get_config['buy_options']

        # If user choices a flat balance, then device the balance by the
        # # closing price.
        if buyOpts['mode'] == 'balance_amount':
            quantity = buyOpts['flat_amount'] / float(closePrice)

        # If user choices a balance percentage, fetch their balance, update the
        # balance to invest by multiplying by the chosen percentage and then
        # devide by the closing price.
        elif buyOpts['mode'] == 'balance_percent':
            balance = self.signalDispatcher.asset_balance(self._tradeCurrency)
            quantity = balance * buyOpts['balance_percent'] / 100 / closePrice

        return self.signalDispatcher.apply_filters(
            self.tradeSymbol,
            quantity
        )

    def run_strategies(self, npCloses: np.array) -> List[dict]:
        """Runs each strategy on collections of closing prices.

        Args:
            npCloses - (np.array) Closing prices.

        Returns:
            A list of there results from running each strategy. Each list item
            will with dictionaries containing a results produced by that
            strategy and a decision.
        """
        stratResults = []
        for strat in self._strategies:
            stratResults.append(strat(self.log).apply_indicator(
                npCloses,
                self.get_config['strategies'][strat.__name__.lower()],
                self.ownCoins
            ))
        return stratResults

    def action_decision(self, close: float, decisions: List[int]) -> None:
        """Using the results, check the buy/sell decisions returned by each
        strategy and take an appropriate action whether that be to do nothing,
        buy or sell.

        Args:
            close - (float) Closing price
            decisions - (int[]) List of decisions.
        """

        if all(decision == 1 for decision in decisions):
            self.log('CONTROLLER: BUY')
            if self._postRequests:
                res = self.signalDispatcher.send_signal(
                    SIDE_BUY,
                    self.tradeSymbol,
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

        elif all(decision == -1 for decision in decisions):
            # Get and sell the entire stock.

            self.log('CONTROLLER: SELL')
            if self._postRequests:
                quantity = self.signalDispatcher.apply_filters(
                    self.tradeSymbol,
                    self.signalDispatcher.asset_balance(
                        self.tradeSymbol.replace(self._tradeCurrency, '')
                    )
                )

                print(f'\033[92mSELLING {quantity}\033[0m')
                res = self.signalDispatcher.send_signal(
                    SIDE_SELL,
                    self.tradeSymbol,
                    quantity,
                    self._testMode
                )

                # Send sell signal
                if res['success']:
                    self.ownCoins = False
                    self._purchasedPrice = 0
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

    def stop_loss(self, close: float) -> None:
        """Attempts to migate any losses by selling coins if the value drops
        below a certain threshold.

        Args:
            close - (float) Closing price.
        """

        if (self.purchasedPrice
                and close <= self.purchasedPrice * self.get_stop_loss()):
            print('\033[92mSELLING TO PREVENT STOP LOSS.\033[0m')

            if self._postRequests:
                quantity = self._signalDispatcher.apply_filters(
                    self.tradeSymbol,
                    self.signalDispatcher.asset_balance(
                        self.tradeSymbol.replace(self.tradeSymbol, '')
                    )
                )
                print(f'\033[92mSELLING {quantity}\033[0m')

                res = self.signalDispatcher.send_signal(
                    SIDE_SELL,
                    self.tradeSymbol,
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

    def update_dataset(self, results: List[dict]) -> None:
        """Logs information from running the strategies into the dataset log.

        Args:
            results - ([dict]) Collection of result dictionaries which should
                contain a `results` and `decision` key with respective values.
        """

        # Create the headers for the dataset csv is it has not already been
        # created.
        if self._createDatasetHead:
            headers = []
            for result in results:
                headers += list(result['results'].keys())

            self.add_dataset('|'.join(headers))
            self._createDatasetHead = False

        # Create a single string from all the results and log.
        resultVals = []
        for result in results:
            resultVals += list(result['results'].values())

        # Casting each element into a string to ensure that there are no
        # `np.float64` datatypes.
        resultVals = [str(result) for result in resultVals]

        # Convert any numpy floats to strings
        self.add_dataset('|'.join(resultVals))
