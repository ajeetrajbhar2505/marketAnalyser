import os
import asyncio
import streamlit as st

from src.prediction.predictor import Predictor
from src.utils.config import load_config

def main():
    st.set_page_config(page_title="Market Analyser", layout="wide")
    st.title("📈 Market Analyser with LLMs")

    config = load_config()
    predictor = Predictor(config)

    symbol = st.text_input("Ticker symbol", value="AAPL")
    horizon = st.slider("Prediction horizon (days)", 1, 5, config.app.prediction_horizon_days)
    refresh = st.checkbox("Force data refresh", False)

    if st.button("Predict"):
        with st.spinner("Running pipeline..."):
            result = asyncio.run(predictor.run(symbol.upper(), horizon, refresh))
        st.success(f"Prediction: {'Bullish' if result.prediction > 0 else 'Bearish'} | Confidence: {result.confidence:.2f}")
        st.metric("Sharpe (backtest)", f"{result.sharpe:.2f}")
        st.json(result.rationale)

if __name__ == "__main__":
    main()
