import yfinance as yf
import pandas as pd
import sqlite3

#tickers for crude oil, gold, wheat
ticker = ["CL=F", "GC=F", "HG=F", "NG=F", "ZW=F"]

#dowload the wide dataframe 
data = yf.download(ticker, period="1mo", interval="1d")

#Moves the tickers down into the rows
data = data.stack(level=1)

#move date from the index label into being a column
data = data.reset_index()

#rename colums to match the exact naming as they are in the SQL table
data = data.rename(columns={"Date": "date", "Ticker": "ticker", "Open": "open_price", "Close": "close_price", "Volume": "volume"})

#Filtering out collumns for SQL table
data = data[["date", "ticker", "open_price", "close_price", "volume"]]

data["date"] = data["date"].dt.strftime("%Y-%m-%d")

rows = data.values.tolist()

conn = sqlite3.connect("src/db/market_data.db")
cursor = conn.cursor()

cursor.executemany("""
    INSERT OR REPLACE INTO daily_futures_prices (date, ticker, open_price, close_price, volume)
    VALUES (?, ?, ?, ?, ?)
""", rows)

conn.commit()
cursor.execute("SELECT COUNT(*) FROM daily_futures_prices")
print("Total rows in vault:", cursor.fetchone()[0])
conn.close()

print("end")