"""Parses arguments for be parsed onto `controller.main`."""

import argparse


def args_parser():
    """Parses arguments for be parsed onto `controller.main`."""

    argsParser = argparse.ArgumentParser(
        description='Arguments for setting up the Binance bot.'
    )
    argsParser.add_argument(
        '-t',
        '--test-mode',
        action='store_true',
        default=False,
        help='Run in test mode?'
    )
    argsParser.add_argument(
        '-m',
        '--buy-mode',
        action='store',
        choices=['balance_amount', 'balance_percent'],
        default='balance_percent',
        help='What buying strategy would you like to use?'
    )
    argsParser.add_argument(
        '-p',
        '--flat-amount',
        action='store',
        help='Flat amount to pay for each buy operation.'
    )
    argsParser.add_argument(
        '-P',
        '--balance-percent',
        action='store',
        help='Percentage of available balance to use during buy operation\
            (25=25%%).'
    )

    args = argsParser.parse_args()

    # Validation
    if args.flat_amount:
        try:
            args.flat_amount = float(args.flat_amount)
        except ValueError:
            raise ValueError(
                'Must be able to cast `--flat-amount` to a float.'
            )

    if args.balance_percent:
        try:
            args.balance_percent = float(args.balance_percent)
        except ValueError:
            raise ValueError(
                'Must be able to cast `--balance-percent` to a float.'
            )

    return args
