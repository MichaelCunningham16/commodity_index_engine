import yfinance as yf
import pandas as pd
import sqlite3

def extract_prices(tickers: list[str]) -> pd.DataFrame:
    # Dowload the wide dataframe 
    df = yf.download(tickers=tickers, period="1mo", interval="1d")
    return df

def transform_prices(raw_df: pd.DataFrame) -> list:
    # Moves the tickers down into the rows
    data = raw_df.stack(level=1)
    # Move date from the index label into being a column
    data = data.reset_index()
    # Rename columns to match the exact naming as they are in the SQL table
    data = data.rename(columns={"Date": "date", "Ticker": "ticker", "Open": "open_price", "Close": "close_price", "Volume": "volume"})
    # Filtering out columns for SQL table
    data = data[["date", "ticker", "open_price", "close_price", "volume"]]
    # Changing the date formatting
    data["date"] = data["date"].dt.strftime("%Y-%m-%d")
    # Strip away column names and row indices and panda overhead, and change numpy array into list
    data = data.values.tolist()
    return data

def upsert_prices(price_data_list: list, db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT OR REPLACE INTO daily_futures_prices (date, ticker, open_price, close_price, volume)
        VALUES (?, ?, ?, ?, ?)
    """, price_data_list)

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM daily_futures_prices")
    print("Total rows in vault:", cursor.fetchone()[0])
    conn.close()


if __name__ == "__main__":
    raw = extract_prices(["CL=F", "GC=F", "HG=F", "NG=F", "ZW=F"])
    clean_data = transform_prices(raw)
    upsert_prices(clean_data, "src/db/market_data.db")