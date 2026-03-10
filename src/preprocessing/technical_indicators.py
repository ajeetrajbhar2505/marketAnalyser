from __future__ import annotations

import pandas as pd


def _pick(df: pd.DataFrame, name: str) -> pd.Series:
    """Pick column by logical name ignoring case/spacing/underscores/ticker suffix."""
    key = name.lower().replace(" ", "").replace("_", "")
    for col in df.columns:
        norm = str(col).lower().replace(" ", "").replace("_", "")
        if norm == key:
            return df[col]
        if norm.endswith(key):  # handle ticker prefixes like msft_close
            return df[col]
    raise KeyError(f"Column '{name}' not found in columns {list(df.columns)}")


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy().reset_index(drop=True)
    close = _pick(df, "close").astype(float).reset_index(drop=True)
    high = _pick(df, "high").astype(float).reset_index(drop=True)
    low = _pick(df, "low").astype(float).reset_index(drop=True)
    volume = _pick(df, "volume").astype(float).reset_index(drop=True)

    # RSI (14)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window=14, min_periods=14).mean()
    loss = -delta.clip(upper=0).rolling(window=14, min_periods=14).mean()
    rs = gain / (loss + 1e-9)
    df["rsi14"] = 100 - (100 / (1 + rs))

    # MACD (12,26,9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # Moving averages
    df["sma20"] = close.rolling(window=20, min_periods=20).mean()
    df["sma50"] = close.rolling(window=50, min_periods=50).mean()
    df["ema20"] = close.ewm(span=20, adjust=False).mean()
    df["ema50"] = close.ewm(span=50, adjust=False).mean()

    # Bollinger Bands (20, 2 std)
    bb_mid = df["sma20"]
    bb_std = close.rolling(window=20, min_periods=20).std()
    df["bb_upper"] = bb_mid + 2 * bb_std
    df["bb_middle"] = bb_mid
    df["bb_lower"] = bb_mid - 2 * bb_std

    # On-Balance Volume
    direction = close.diff().fillna(0).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    df["obv"] = (direction * volume).cumsum()

    # Clean
    df = df.replace([float("inf"), float("-inf")], pd.NA)
    df = df.dropna()
    return df
