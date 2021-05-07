"""Script to show visual representation of the datasets that have been logged.
"""

import os
import numpy as np
import pandas as pd


fileName = input('Dataset file name: ')
csvPath = os.path.join('bot', 'logs', fileName)
df = pd.read_csv(csvPath, sep='|')


rsiBuy = []
rsiSell = []
bollBuy = []
bollSell = []
signalBuy = []
signalSell = []

for i in range(len(df['Close'])):

    # RSI
    if df['RSI Decision'].iloc[i] == 0:
        rsiBuy.append(np.nan)
        rsiSell.append(np.nan)

    elif df['RSI Decision'].iloc[i] == 1:
        rsiBuy.append(df['Close'].iloc[i])
        rsiSell.append(np.nan)

    elif df['RSI Decision'].iloc[i] == -1:
        rsiBuy.append(np.nan)
        rsiSell.append(df['Close'].iloc[i])

    # Bollinger
    if df['Bollinger Decision'].iloc[i] == 0:
        bollBuy.append(np.nan)
        bollSell.append(np.nan)

    elif df['Bollinger Decision'].iloc[i] == 1:
        bollBuy.append(df['Close'].iloc[i])
        bollSell.append(np.nan)

    elif df['Bollinger Decision'].iloc[i] == -1:
        bollBuy.append(np.nan)
        bollSell.append(df['Close'].iloc[i])

    # Buy/Sell Signals
    if df['RSI Decision'].iloc[i] == 0 or df['Bollinger Decision'].iloc[i] == 0:
        signalBuy.append(np.nan)
        signalSell.append(np.nan)

    elif df['RSI Decision'].iloc[i] == 1 and df['Bollinger Decision'].iloc[i] == 1:
        signalBuy.append(df['Close'].iloc[i])
        signalSell.append(np.nan)

    elif df['RSI Decision'].iloc[i] == -1 and df['Bollinger Decision'].iloc[i] == -1:
        signalBuy.append(np.nan)
        signalSell.append(df['Close'].iloc[i])

plt.style.use('fivethirtyeight')
fig, ax = plt.subplots()

df['RSI Buy'] = np.array(rsiBuy)
df['RSI Sell'] = np.array(rsiSell)
df['Boll Buy'] = np.array(bollBuy)
df['Boll Sell'] = np.array(bollSell)
df['Signal Buy'] = np.array(signalBuy)
df['Signal Sell'] = np.array(signalSell)

ax.plot(df['Timestamp'], df['Close'], color='royalblue')

# Plot Bollinger
ax.fill_between(df['Timestamp'], df['Bollinger High'],
                df['Bollinger Low'], color='grey', alpha=0.5)
plt.grid()

ax2 = ax.twinx()

ax.plot(df['Timestamp'], df['RSI Buy'], 'g.', markersize=4)
ax.plot(df['Timestamp'], df['RSI Sell'], 'r.', markersize=4)
ax.plot(df['Timestamp'], df['Boll Buy'], 'g*', markersize=4)
ax.plot(df['Timestamp'], df['Boll Sell'], 'r*', markersize=4)
ax.plot(df['Timestamp'], df['Signal Buy'], 'g^', markersize=10)
ax.plot(df['Timestamp'], df['Signal Sell'], 'r^', markersize=10)

ax2.plot(df['Timestamp'], df['RSI Value'], lw=.75, alpha=0.5, color='purple')

plt.show()
