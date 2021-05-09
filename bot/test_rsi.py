import os
import numpy as np
from strategies import RSI
from send_order_signal import SendOrderSignal
from binance.client import Client
from datetime import datetime
import time

signal = SendOrderSignal()
client = signal.get_client()

historicalData = client.get_historical_klines(
    'ETHGBP',
    Client.KLINE_INTERVAL_1MINUTE,
    '120 mins ago UTC'
)

config = {
    'period': 14,
    'overbought_limit': 70,
    'oversold_limit': 30
}
coinsOwned = False

f = open('tmp.csv', 'w+')
closes = []

for data in historicalData:
    print(data[6])
    s, ms = divmod(int(data[6]), 1000)
    timestamp = '%s.%03d' % (time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(s)), ms)
    close = float(data[4])
    closes.append(close)
    rsi = RSI().apply_indicator(np.array(closes), config, coinsOwned)
    f.write(f"{timestamp}|{close}|{rsi['results']['RSI Value']}|{rsi['decision']}")

