from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

import backoff
import pandas as pd
import yfinance as yf
from loguru import logger

from src.utils.cache import TTLCache
from src.utils.config import Settings


class StockDataFetcher:
    def __init__(self, config: Settings, cache: Optional[TTLCache] = None):
        self.config = config
        self.cache = cache or TTLCache(config.app.cache_ttl_seconds)

    @backoff.on_exception(backoff.expo, Exception, max_time=60)
    def fetch_history(self, symbol: str, years: int = 5, interval: str = "1d", force_refresh: bool = False) -> pd.DataFrame:
        cache_key = f"history:{symbol}:{interval}:{years}"
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return pd.DataFrame(cached)

        end = dt.datetime.utcnow()
        start = end - dt.timedelta(days=365 * years)
        logger.info(f"Downloading {symbol} history from {start.date()} to {end.date()} at {interval}")
        try:
            data = yf.download(symbol, start=start, end=end, interval=interval, progress=False, group_by="ticker")
        except Exception as exc:
            logger.warning(f"yfinance download failed ({exc}); attempting local fallback.")
            data = pd.DataFrame()

        fallback_path = Path(f"data/raw/{symbol.lower()}.csv")
        if data.empty and fallback_path.exists():
            logger.info(f"Loading cached prices from {fallback_path}")
            data = pd.read_csv(fallback_path, parse_dates=[0])

        if data.empty:
            raise ValueError(f"No price data returned for {symbol}. Check connectivity or provide cached data at {fallback_path}.")

        if isinstance(data.columns, pd.MultiIndex):
            tickers = data.columns.get_level_values(0).unique()
            fields = data.columns.get_level_values(1).unique()
            # If single ticker, drop ticker prefix and keep field names
            if len(tickers) == 1 and len(fields) > 0:
                data.columns = [col[1].lower() for col in data.columns]
            else:
                data.columns = [f"{col[0].lower()}_{col[1].lower()}" for col in data.columns]
        else:
            data.columns = [c.lower() for c in data.columns]

        data = data.reset_index()
        data.columns = [str(c).lower() for c in data.columns]

        if not data.empty:
            self.cache.set(cache_key, data.to_dict(orient="list"))
        return data

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def fetch_quote(self, symbol: str) -> pd.Series:
        cache_key = f"quote:{symbol}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return pd.Series(cached)

        ticker = yf.Ticker(symbol)
        info = ticker.history(period="1d").tail(1)
        if info.empty:
            raise ValueError(f"No quote found for {symbol}")
        last_row = info.iloc[0]
        series = pd.Series({
            "price": float(last_row["Close"]),
            "open": float(last_row["Open"]),
            "high": float(last_row["High"]),
            "low": float(last_row["Low"]),
            "volume": int(last_row["Volume"]),
            "asof": str(info.index[0]),
        })
        self.cache.set(cache_key, series.to_dict())
        return series
