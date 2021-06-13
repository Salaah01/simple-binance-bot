#!/usr/bin/python3

"""Loads historical kline data onto the database."""
import os
import re
import csv
import traceback
from datetime import datetime, timedelta
from psycopg2.errors import UniqueViolation
from db_connection import connection
from epoch_to_datetime import epoch_to_datetime

KLINES_DIRS = [
    '/mnt/d/Documents/Trading/Programs/binance-public-data/data/data'
    # 'D:\\Documents\\Trading\\Programs\\binance-public-data\\data\\data'
    # os.path.join('C:', os.sep, 'Users', 'amins4',
    #              'Downloads', 'hist_klines', 'hist_klines')

]
conn = connection()
cur = conn.cursor()

# Fetch all the currently loaded files and symbols.
cur.execute('SELECT file FROM loaded_files')
loadedFiles = set([f[0] for f in cur.fetchall()])
cur.execute('SELECT symbol FROM symbols')
symbols = set([s[0] for s in cur.fetchall()])

# Collect all the files to load.
files = []
for klineDir in KLINES_DIRS:
    for _file in os.listdir(klineDir):
        if _file not in loadedFiles:
            files.append(os.path.join(klineDir, _file))

# Load each file
totalFiles = len(files)

# The format of each CSV is the following by column index:
# 0 - Open time
# 1 - Open
# 2 - High
# 3 - Low
# 4 - Close
# 5 - Volume
# 6 - Close time
# 7 - Quote asset volume
# 8 - Number of trades
# 9 - Taker buy base asset volume
# 10 - Taker buy quote asset volume
# 11 - Ignore

insertSQL = """
            (symbol, open_time, open_price, high_price, low_price, close_price,
             volume, close_time, quote_asset_volume, no_traders,
             taker_buy_base_asset_vol, taker_buy_quote_asset_vol)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

for fID, _file in enumerate(files):
    print(f'Processing {fID+1}/{totalFiles} files, 0% done.', end='\r')

    # Load the symbol if it does not exist.
    symbol = re.search('[A-Z]{5,}', _file)[0]
    if symbol not in symbols:
        cur.execute('INSERT INTO symbols VALUES (%s)', (symbol,))
        symbols.add(symbol)

    # Load the data
    with open(_file) as csvFile:
        reader = csv.reader(csvFile)

        for row in reader:
            if not reader.line_num % 1000 or reader.line_num == 44640:
                progress = f'{round(reader.line_num / 44640 * 100)}%'
                print(
                    f'Processing {fID+1}/{totalFiles} files, {progress} done.',
                    end='\r'
                )
            row = [float(r) for r in row]

            # Convert the rows with epoch time to timestamps.
            for idx in [0, 6]:
                row[idx] = epoch_to_datetime(row[idx])

            # Due to the csv epoch's being in scientific notation, some
            # accuracy is lost. Therefore, we will manually set the time
            # based on the row number.
            row[0] = datetime.combine(
                row[0],
                datetime.min.time()
            ) + timedelta(minutes=reader.line_num)
            row[6] = datetime.combine(
                row[6],
                datetime.min.time()
            ) + timedelta(minutes=reader.line_num - 1)

            if re.findall(r'\d{1,}m', _file)[0] == '1m':
                insertLine = 'INSERT INTO prices_1m\n'
            else:
                insertLine = 'INSERT INTO prices_5m\n'

            try:
                cur.execute(insertLine + insertSQL, [symbol] + row[0: -1])
            except UniqueViolation:
                pass
            except Exception:
                conn.rollback()
                print(f'\nFailing row: {row}')
                raise Exception(traceback.format_exc())
            finally:
                conn.commit()

        cur.execute(
            "INSERT INTO loaded_files VALUES (%s)",
            (_file.split(os.sep)[-1],)
        )
        conn.commit()
