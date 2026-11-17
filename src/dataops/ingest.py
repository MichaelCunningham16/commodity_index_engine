import yfinance as yf
import pandas as pd
import sqlite3
import logging

logging.basicConfig(filename="app.log", encoding="utf-8", filemode="a", format="{asctime} - {levelname} - {message}", style="{", datefmt="%Y-%m-%d %H:%M", level=logging.INFO)

def extract_prices(tickers: list[str]) -> pd.DataFrame:
    try:
        # Dowload the wide dataframe 
        df = yf.download(tickers=tickers, period="1mo", interval="1d")
        return df
    except Exception as e:
        logging.error(f"Error downloading dataframe: {e}") 

def transform_market_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    # Moves the tickers down into the rows
    clean_df = raw_df.stack(level=1)
    # Move date from the index label into being a column
    clean_df = clean_df.reset_index()
    # Rename columns to match the exact naming as they are in the SQL table
    clean_df = clean_df.rename(columns={"Date": "date", "Ticker": "ticker", "Open": "open_price", "Close": "close_price", "Volume": "volume"})
    # Filtering out columns for SQL table
    clean_df = clean_df[["date", "ticker", "open_price", "close_price", "volume"]]
    # Changing the date formatting
    clean_df["date"] = clean_df["date"].dt.strftime("%Y-%m-%d")
    return clean_df

def transform_positions(clean_data: pd.DataFrame) -> pd.DataFrame:
    #Dictonary for index weights
    weight_map = {"CL=F": 0.2, "GC=F": 0.3, "HG=F": 0.1, "NG=F": 0.05, "ZW=F": 0.35}

    pos_df = clean_data[["date", "ticker"]].copy()

    # Adding columns for index names and weights (currently based on predefined dictonary)
    pos_df["index_name"] = "COMMODITY_CORE"
    pos_df["weight"] = pos_df["ticker"].map(weight_map)

    # Rearranging order of columns to match expected SQL table order
    pos_df = pos_df[["date", "index_name", "ticker", "weight"]]
    return pos_df

def upsert_market_data(clean_df: pd.DataFrame, pos_df: pd.DataFrame, db_path: str) -> None:

    # Strip away column names and row indices and panda overhead, and change numpy array into list
    price_data_list = clean_df.values.tolist()
    index_data_list = pos_df.values.tolist()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executemany("""
        INSERT OR REPLACE INTO daily_futures_prices (date, ticker, open_price, close_price, volume)
        VALUES (?, ?, ?, ?, ?)
    """, price_data_list)

    cursor.executemany("""
            INSERT OR REPLACE INTO daily_index_positions (date, index_name, ticker, weight)
            VALUES (?, ?, ?, ?)
        """, index_data_list)

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM daily_futures_prices")
    logging.info(f"Total rows in table 1:, {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM daily_index_positions")
    logging.info(f"Total rows in table 2:, {cursor.fetchone()[0]}")
    conn.close()

if __name__ == "__main__":
    raw = extract_prices(["CL=F", "GC=F", "HG=F", "NG=F", "ZW=F"])
    if raw is None or raw.empty:
        logging.error("Error with dowloaded dataframe")
    else:
        clean_data = transform_market_data(raw)
        index_data = transform_positions(clean_data)
        upsert_market_data(clean_data, index_data, "src/db/market_data.db")

