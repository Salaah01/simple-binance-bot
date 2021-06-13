"""Main controller that will maintain the connection, and send buy/sell
singals
"""

import time
import json
import os
from datetime import datetime, timedelta
from copy import deepcopy
from multiprocessing import Process
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


def run_trader(config: dict, tradeSymbol: str, seed: int) -> None:
    """Runs an instance of the trader.

    Args:
        config - (dict) Config dict.
        tradeSymbol - (str) Trade symbol to trade in.
        seed - (int) Seed number for selecting strategies to run.
    """
    Trader(config, tradeSymbol, seed).run()


def main():
    # Limits the number of coins to trade in, this is to prevent IP bans or
    # having to timeout before sending further API requests.
    NO_COINS_TO_TRADE = 20

    config = load_config(args_parser())

    processes = []

    # To prevent an IP ban between each connection, we will simulate a delay
    # pause before each connection.
    tradeSyms = set(config['trade_symbols'])

    # In test mode use only 1 coin.
    if config['testing']['testing']:
        tradeSyms = config['trade_symbols'][0: 1]

    delaySecs = 5

    totalSyms = min(len(tradeSyms), NO_COINS_TO_TRADE)

    reqWaitTimeLoc = os.path.abspath(
        os.path.join(
            __file__,
            os.pardir,
            'request_wait_time.txt'
        )
    )

    if not os.path.isfile(reqWaitTimeLoc):
        with open(reqWaitTimeLoc, 'w+') as f:
            f.write(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S'))

    for idx, tradeSymbol in enumerate(tradeSyms):

        if idx == NO_COINS_TO_TRADE:
            break

        process = Process(
            target=run_trader,
            args=[config, tradeSymbol, idx % 2]
        )
        process.start()
        processes.append(process)

        print(
            f'{idx+1} of {totalSyms} Set up. ETA: {timedelta(seconds=(totalSyms-idx+1)*delaySecs)}',  # noqa: E501
            end='\r'
        )
        time.sleep(delaySecs)

    for process in processes:
        process.join()


if __name__ == '__main__':
    main()
