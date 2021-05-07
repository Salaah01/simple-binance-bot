"""Connects and sends signals to the Binance server."""

import math
import json
import traceback
from binance.client import Client
from binance.enums import ORDER_TYPE_MARKET


class SendOrderSignal:
    """Connects and sends signals to the Binance server."""

    def __init__(self):
        self._client = self._set_client()

    @staticmethod
    def _set_client():
        """Set the client object to connect to Binance."""
        with open('.keys.json', 'r') as keysFile:
            keys = json.load(keysFile)

        return Client(keys['BINANCE_API_KEY'], keys['BINANCE_SECRET_KEY'])

    def get_client(self):
        """Returns the client object."""
        return self._client

    def send_signal(
        self,
        side: str,
        tradeSymbol: str,
        quantity: float,
        testMode: bool,
        orderType=ORDER_TYPE_MARKET,
    ):
        """Sends an order to buy/sell.

        Args:
            side - (str) Buy or sell command.
            tradeSymbol - (str) Trade symbol.
            quantity - (float) Quantity.
            testMode: (bool) Run in test mode? If `True`, this will not create
                live orders.
            orderType - (str) Order type, limit, market, etc.
        """

        # Set the order method to use based on whether the order is a test
        # order or not.
        if testMode:
            order = self.get_client().create_test_order
        else:
            order = self.get_client().create_order

        try:
            print("\033[94mSENDING SIGNAL.\033[0m")
            res = order(
                symbol=tradeSymbol,
                side=side,
                type=orderType,
                quantity=quantity
            )

            return {
                'success': bool(res.get('clientOrderId')),
                'results': res
            }

        except Exception:
            return {
                'success': False,
                'params': {
                    'side': side,
                    'quantity': quantity
                },
                'error': traceback.format_exc()
            }

    def apply_filters(self, tradeSymbol, quantity):
        filters = self.get_client().get_symbol_info(tradeSymbol)['filters']
        for filt in filters:
            if filt['filterType'] == 'LOT_SIZE':
                stepSize = float(filt['stepSize'])

                # Adding an higher level round to remove any floating point
                # errors.
                return round(math.floor(quantity / stepSize) * stepSize, 6)
        else:
            return quantity

    def asset_balance(self, asset: str):
        """Fetch the asset balance.

        Args:
            asset - (str) Asset name.
        """
        return float(self.get_client().get_asset_balance(asset=asset)['free'])
