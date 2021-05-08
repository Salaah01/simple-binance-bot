# Simple Binance Bot
A very simple bot that trades in the Binance market.

## Strategies
The bot uses RSI and Bollinger to estimate the best time to buy and sell
assets.
Characteristics such as length/period for analysing data can be accessed and
updated from `./bot/config.json`.

## Setup
### Binance
* Create a [Binance account](https://www.binance.com/en/register?ref=135385561).
* Enable Two-Factor Authentication
* Create a new set of API keys.
* Deposit some money or buy some cryptocurrency. Either some form of balance or currency is needed for the bot to be able to buy/sell.

### Bot
1. Create a the file `./bot/.keys.json` and add your API keys. Example below:
```json
{
  "BINANCE_API_KEY": "<BINANCE_API_KEY>",
  "BINANCE_SECRET_KEY": "<BINANCE_SECRET_KEY>"
}
```
2. If you are using Linux/UNIX, I recommend changing the permissions of the created file to 600 for added security: `chmod 600 ./bot/.keys.json`.

3. If you are using Docker, then go to step 4, otherwise, skip step 4.

4. Build the docker image: `docker-compose up --build`. Skip the rest of the steps (Isn't Docker great?)
5. Install [TA-Lib](https://github.com/mrjbq7/ta-lib). The process differs depending on your OS, so please read the documentation.
6. Create a virtual environment. `python -m venv venv`.
7. Activate the virtual environment:
**Linux:** `venv/bin/activate`.
**Windows (Powershell):** `venv\Scripts\Activate`.
1. Install Python packages: `pip install -r ./bot/requirements.txt`.

## Running (and Testing) Bot
If you are using Docker, you would need to ensure that the containers are running. To run the containers, `docker-compose up`. Once you have started containers, you can run `bash bot_shell.sh` that will connect you to the bot container into a bash shell.

For those who are not using docker: `cd bot`.

As the name suggests, `controller.py` controls most of the automation. In order to start testing/running run `python controller.py` followed by args. To see a full, up-to-date list of the args, run `python controller.py -h`.

**Usage**
```
usage: controller.py [-h] [-t] [-m {balance_amount,balance_percent}]
                     [-p FLAT_AMOUNT] [-P BALANCE_PERCENT] -s TRADE_SYMBOL -A
                     ASSET [-o]

Arguments for setting up the Binance bot.

optional arguments:
  -h, --help            show this help message and exit
  -t, --test-mode       Run in test mode?
  -m {balance_amount,balance_percent}, --buy-mode {balance_amount,balance_percent}
                        What buying strategy would you like to use?
  -p FLAT_AMOUNT, --flat-amount FLAT_AMOUNT
                        Flat amount to pay for each buy operation.
  -P BALANCE_PERCENT, --balance-percent BALANCE_PERCENT
                        Percentage of available balance to use during buy
                        operation (25=25%).
  -s TRADE_SYMBOL, --trade-symbol TRADE_SYMBOL
                        Trade symbol.
  -A ASSET, --asset ASSET
                        Asset.
  -o, --coin-owned      Coin is owned.
```

**Configuration**
Most of the configurations is handled by `./bot/config.json`.
Below is a outline of each configuration.

```json
{
  "defaults": {
    "interval": "<< Interval e.g: << 1m, 3m, 5m, 4h >>",
    "socket_address": "THIS SHOULD NOT BE CHANGED.",
    "stop_loss_percent": "<< Stop loss percentage. 10 = 10%.",
    "closes_array_size": "THIS SHOULD NOT BE CHANGED."
  },
  "buy_options": {
    "test_mode": "Running on test mode? (bool)", 
    "mode": "Trading mode. 'balance_percent' or 'balance_percent'"
  },
  "strategies": {
    "rsi": {
      "period": "RSI period as an integer. e.g: 14",
      "overbought_limit": "RSI upper limit (overbought). e.g: 70",
      "oversold_limit": "RSI lower limit (oversold). e.g: 30"
    },
    "bollinger": {
      "period": "Bollinger period. e.g: 20",
    }
  },
  "testing": {
    "testing": "Running on test most? - (bool)",
    "post_requests": "Send post requests during test most? (bool)"
  },
  "trade_currencies": [
    "Currencies to trade in:",
    "GBP",
    "USDT"
  ],
  "trade_symbols": [
    "ETCUSDT",
    "EOSUSDT",
    "QTUMUSDT",
    "THETAUSDT",
    "CTSIUSDT",
    "ONTUSDT",
    "ZENUSDT",
    "STORJUSDT",
    "REEFUSDT",
    "ZECUSDT"
  ]
}
```

## Disclaimer
You are free to use this program as you wish but must understand the risks associated with using the program. I do not have a financial background and have no authority in advising when it is best to buy/sell assets.

As such, I do not guarantee that you will make money and warn you that you may in fact lose money.

Under no circumstances will I or any other contributor be held responsible or liable in any way for any claims, damages, losses, expenses or any other liabilities whatsoever.

By using this program you acknowledge that you so at your own risk.
