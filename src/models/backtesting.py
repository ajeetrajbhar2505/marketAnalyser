from __future__ import annotations

import numpy as np
import pandas as pd


def backtest(prices: pd.Series, signals: pd.Series, initial_capital: float = 100000, transaction_cost: float = 0.0005, slippage: float = 0.0002) -> dict:
    if prices.empty or signals.empty:
        return {"sharpe": 0.0, "returns": []}

    positions = signals.shift(1).fillna(0)
    returns = prices.pct_change().fillna(0)
    strategy_returns = positions * returns - transaction_cost - slippage
    equity_curve = (1 + strategy_returns).cumprod() * initial_capital
    sharpe = np.sqrt(252) * strategy_returns.mean() / (strategy_returns.std() + 1e-6)
    return {
        "sharpe": float(sharpe),
        "equity_curve": equity_curve.tolist(),
        "final_value": float(equity_curve.iloc[-1]),
    }
