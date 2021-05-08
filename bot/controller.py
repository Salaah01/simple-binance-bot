"""Main controller that will maintain the connection, and send buy/sell
singals
"""

import json
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


def run_trader(config: dict, tradeSymbol: str):
    Trader(config, tradeSymbol).run()


def main():
    config = load_config(args_parser())

    processes = []
    for tradeSymbol in set(config['trade_symbols']):
        process = Process(target=run_trader, args=[config, tradeSymbol])
        process.start()
        processes.append(process)

    for process in processes:
        process.join()


if __name__ == '__main__':
    main()
