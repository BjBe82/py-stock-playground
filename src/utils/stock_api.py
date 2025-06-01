from functools import lru_cache

import pandas as pd
import yfinance as yf


@lru_cache(maxsize=100)
def get_history(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    print(f"Downloading data for {ticker} from {start_date} to {end_date}")
    nasdaq = yf.Ticker(ticker)
    return nasdaq.history(start=start_date, end=end_date, interval="1d")
