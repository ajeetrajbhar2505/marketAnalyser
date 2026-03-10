<<<<<<< HEAD
# marketAnalyser
=======
# Stock Prediction with LLMs

Production-ready scaffold for a modular stock prediction system combining market data, news/social sentiment, technical indicators, and LLM analysis.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m nltk.downloader stopwords
python main.py --symbol AAPL
```

Run dashboard:
```bash
streamlit run src/visualization/dashboard.py
```

## Configuration
Edit `config/config.yaml` for API keys, toggles, and model settings. Environment variables in the file are resolved by your shell.

## Structure
- `src/data_collection`: yfinance/Reuters/social ingestion with caching and rate-limit backoff
- `src/preprocessing`: text cleaning, TA indicators
- `src/models`: LLM scoring, ensemble classifier, backtesting
- `src/prediction`: pipeline orchestrator
- `src/visualization`: Streamlit UI
- `tests`: add unit tests to target >80% coverage

## Notes
- LLM default is `gpt2` placeholder; swap with a finance-tuned checkpoint.
- Social/Twitter/Reddit/news APIs are optional; enable and add keys in config.
- Includes simple Sharpe backtest; extend with position sizing and risk controls.
- Not financial advice; outputs are probabilistic signals.
>>>>>>> 79f9710 (minor changes)
