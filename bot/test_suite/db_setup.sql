-- Running the following SQL to create the tables if the database has not
-- been set up yet.
CREATE TABLE symbols (symbol VARCHAR(10) PRIMARY KEY);
CREATE TABLE prices (
  id SERIAL PRIMARY KEY,
  open_time TIMESTAMP,
  symbol VARCHAR(10),
  open_price FLOAT,
  high_price FLOAT,
  low_price FLOAT,
  close_price FLOAT,
  volume FLOAT,
  close_time TIMESTAMP,
  quote_asset_volume FLOAT,
  no_traders INTEGER,
  taker_buy_base_asset_vol FLOAT,
  taker_buy_quote_asset_vol FLOAT,
  CONSTRAINT fk_symbol FOREIGN KEY(symbol) REFERENCES symbols(symbol),
  UNIQUE (open_time, symbol)
);
CREATE TABLE loaded_files(file VARCHAR(100) PRIMARY KEY UNIQUE);