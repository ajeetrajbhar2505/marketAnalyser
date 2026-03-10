from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from src.data_collection.news_scraper import NewsScraper
from src.data_collection.social_media import SocialCollector
from src.data_collection.stock_data import StockDataFetcher
from src.models.backtesting import backtest
from src.models.ensemble_model import EnsembleModel
from src.models.llm_model import LLMScorer
from src.preprocessing.technical_indicators import add_indicators
from src.preprocessing.text_processor import batch_clean
from src.utils.cache import TTLCache
from src.utils.config import Settings
from src.utils.logging import logger


@dataclass
class PredictionResult:
    symbol: str
    horizon_days: int
    prediction: float
    confidence: float
    sharpe: float
    rationale: Dict[str, float]

    def json(self, indent: int | None = None) -> str:
        import json

        return json.dumps(self.__dict__, indent=indent)


class Predictor:
    def __init__(self, config: Settings):
        self.config = config
        self.cache = TTLCache(ttl_seconds=config.app.cache_ttl_seconds, redis_url=config.redis.url if config.redis.enabled else None)
        self.stock_fetcher = StockDataFetcher(config, cache=self.cache)
        self.news_scraper = NewsScraper(config, cache=self.cache)
        self.social_collector = SocialCollector(config, cache=self.cache)
        self.llm_scorer = LLMScorer(config)
        self.ensemble = EnsembleModel()


    async def run(self, symbol: str, horizon_days: int, force_refresh: bool = False) -> PredictionResult:
        price_df = await asyncio.to_thread(self.stock_fetcher.fetch_history, symbol, self.config.app.backtest_years, "1d", force_refresh)
        indicators = add_indicators(price_df)
        price_df = indicators

        news_articles = await asyncio.to_thread(self.news_scraper.fetch_news, symbol, 3, force_refresh)
        social_posts = await asyncio.to_thread(self.social_collector.fetch, symbol, 50, force_refresh)

        texts = [n["title"] + " " + n.get("summary", "") for n in news_articles] + [s["text"] for s in social_posts]
        clean_texts = batch_clean(texts)
        sentiments = self.llm_scorer.score_sentences(clean_texts)

        if not price_df.empty:
            price_df["sentiment"] = np.clip(np.mean(sentiments) if sentiments else 0.0, -1, 1)
        else:
            price_df = pd.DataFrame()

        if price_df.empty:
            raise ValueError("Price dataframe is empty; cannot generate prediction")

        # target: next-day direction
        price_df["target"] = np.sign(price_df["close"].pct_change(horizon_days)).shift(-horizon_days)
        price_df = price_df.dropna()
        feature_cols = [col for col in price_df.columns if col not in ["date", "target"]]
        X = price_df[feature_cols].values
        y = price_df["target"].values

        fit_res = self.ensemble.fit(X, y)
        latest_features = X[-1:]
        proba = self.ensemble.predict_proba(latest_features)[0]
        classes = list(getattr(self.ensemble, "clf", self.ensemble.clf).classes_)
        up_index = classes.index(1) if 1 in classes else int(np.argmax(proba))
        up_conf = float(proba[up_index])
        direction = 1 if up_conf >= 0.5 else -1

        bt = backtest(price_df["close"], pd.Series(self.ensemble.predict(X), index=price_df.index), self.config.backtest.initial_capital, self.config.backtest.transaction_cost, self.config.backtest.slippage)

        val_acc = None
        if isinstance(fit_res, dict):
            val_acc = fit_res.get("val_accuracy", fit_res.get("train_accuracy"))
        else:
            val_acc = getattr(fit_res, "accuracy", None)

        return PredictionResult(
            symbol=symbol,
            horizon_days=horizon_days,
            prediction=float(direction),
            confidence=up_conf,
            sharpe=bt["sharpe"],
            rationale={
                "news_count": len(news_articles),
                "social_count": len(social_posts),
                "model_val_accuracy": val_acc,
            },
            
            
        )
    
    
