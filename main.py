"""Entry point for the stock prediction LLM system."""
import argparse
import asyncio
from pathlib import Path

from src.prediction.predictor import Predictor
from src.utils.config import load_config
from src.utils.logging import configure_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stock prediction LLM pipeline")
    parser.add_argument("--symbol", required=True, help="Ticker symbol, e.g., AAPL")
    parser.add_argument("--days", type=int, default=None, help="Prediction horizon override (days)")
    parser.add_argument("--refresh", action="store_true", help="Force refresh of cached data")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()
    configure_logging(config.app.log_level)

    horizon = args.days or config.app.prediction_horizon_days
    predictor = Predictor(config)

    result = asyncio.run(predictor.run(symbol=args.symbol.upper(), horizon_days=horizon, force_refresh=args.refresh))
    print("\nPrediction result:")
    print(result.json(indent=2))


if __name__ == "__main__":
    main()
