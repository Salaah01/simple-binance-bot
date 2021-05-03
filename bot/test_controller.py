"""Unittests for the `Controller` class."""

import unittest
from types import SimpleNamespace
from controller import Controller


class SignalDispatcherOveride:
    """Overwrites the signal dispatcher class for testing."""

    @staticmethod
    def get_asset_balance(_):
        return 100

    @staticmethod
    def apply_filters(_, quantity: float):
        return round(quantity, 6)

    @staticmethod
    def send_signal(*args, **kwargs):
        return {'success': False, 'error': 'THIS IS THE ERROR'}


class TestController(unittest.TestCase):
    """Unittests for the `Controller` class."""

    def setUp(self):
        self.options = SimpleNamespace(
            test_mode=True,
            buy_mode='balance_percent',
            flat_amount=10.99,
            balance_percent=75.54,
            trade_symbol='ETHGBP',
            asset='GBP',
            coin_owned=False
        )

    @staticmethod
    def controller(options: SimpleNamespace):
        """Instantiates the `Controller` object overriding certain methods.

        Args:
            options - (SimpleNamesspace) Set of config. option that would be
                normtally provided by the CLI.
        """

        ctrl = Controller(options)
        ctrl._signalDispatcher = SignalDispatcherOveride()

        return ctrl

    @staticmethod
    def strats_return(returnVal: int):
        """Override method for strategies.

        Args:
            returnVal - (int) Return value.
        """
        def stratsReturn(*args, **kwargs):
            return SimpleNamespace(decision=returnVal)

        return stratsReturn

    def test_config(self):
        """Check that the config is set up correctly."""
        controller = Controller(self.options)
        config = controller.get_config()

        self.assertEqual(
            config['defaults'],
            {
                'asset': 'GBP',
                'trade_symbol': 'ETHGBP',
                'interval': '1m',
                'socket_address': 'wss://stream.binance.com:9443/ws/ethgbp@kline_1m'
            }
        )

        self.assertEqual(
            config['buy_options'],
            {
                'test_mode': True,
                'mode': 'balance_percent',
                'flat_amount': 10.99,
                'balance_percent': 75.54
            }
        )

    def test_buy_quantity_flat_amount(self):
        """Tests that a valid buy quantity is returned with a flat amount."""
        self.options.buy_mode = 'balance_amount'
        controller = self.controller(self.options)
        quantity = controller.buy_quantity(10)
        self.assertEqual(quantity, 1.099)

    def test_buy_quantity_bal_percent(self):
        """Tests that a valid buy quantity is returned with with the buying
        option set to balance percent.
        """

        controller = self.controller(self.options)
        quantity = controller.buy_quantity(10)
        self.assertEqual(quantity, 7.554)


if __name__ == '__main__':
    unittest.main()
