"""Sells all the coins."""

import sys
import os
import json
import traceback
from binance.enums import SIDE_SELL
ROOT = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
sys.path.append(ROOT)
from bot.send_order_signal import SendOrderSignal  # noqa: E402

TEST_MODE = True


# Load variables from config file.
with open(os.path.join(ROOT, 'bot', 'config.json')) as jsonFile:
    CONFIG = json.load(jsonFile)

tradeSymbols = CONFIG['trade_symbols']
tradeCurrencies = CONFIG['trade_currencies']

signal = SendOrderSignal()
failedCoins = []
for tradeSymbol in tradeSymbols:
    try:
        # Remove the currency from the coin name.
        symbol = tradeSymbol
        for tradeCurrency in tradeCurrencies:
            symbol = symbol.rstrip(tradeCurrency)

        # Check the asset balance
        balance = signal.asset_balance(symbol)
        signal.respect_request_limit()

        # If there is no balance, move onto the next coin.
        if not float(balance):
            continue

        # Sell the assets.
        res = signal.send_signal(SIDE_SELL, tradeSymbol, balance, TEST_MODE)
        signal.respect_request_limit()
        if res['success']:
            print(f'\033[92mSold {tradeSymbol}\033[0m')
        else:
            print(F'\033[0mFAILED TO SELL {tradeSymbol}\033[0m')
            failedCoins.append(tradeSymbol)
    except Exception:
        print(traceback.format_exc())
        print(f'\033[91m FAILED TO SELL {tradeSymbol}.\033[91m')
        failedCoins.append(tradeSymbol)


# Print out any failed coins that need to be sold separately.
if failedCoins:
    print(f'Failed to sell {len(failedCoins)} coins: {failedCoins}')
