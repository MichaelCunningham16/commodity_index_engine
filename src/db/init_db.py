import sqlite3

#Opens the connection
conn = sqlite3.connect("src/db/market_data.db") #Makes the market_data file and connects to it

cursor = conn.cursor()

#executing sql strings
#Table 1 for the future prices
cursor.execute("""
CREATE TABLE IF NOT EXISTS daily_futures_prices (
    date DATE,
    ticker VARCHAR,
    open_price FLOAT,
    close_price FLOAT,
    volume BIGINT,
    PRIMARY KEY (date, ticker)
);
""")

#table 2 for the index positions
cursor.execute("""
CREATE TABLE IF NOT EXISTS daily_index_positions (
    date DATE,
    index_name VARCHAR,
    ticker VARCHAR,
    weight FLOAT,
    PRIMARY KEY (date, ticker, index_name)
);
""")

