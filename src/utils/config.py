from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel


class AppSettings(BaseModel):
    name: str
    log_level: str = "INFO"
    cache_ttl_seconds: int = 900
    prediction_horizon_days: int = 3
    backtest_years: int = 5


class Paths(BaseModel):
    raw_data: Path
    processed_data: Path
    database: Path


class APISettings(BaseModel):
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    bearer_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    user_agent: Optional[str] = None
    enabled: bool = False


class APIConfig(BaseModel):
    yfinance: APISettings
    alpha_vantage: APISettings
    news_api: APISettings
    twitter: APISettings
    reddit: APISettings


class DatabaseConfig(BaseModel):
    url: str
    echo: bool = False


class LLMConfig(BaseModel):
    provider: str
    model_name: str
    max_tokens: int = 256
    temperature: float = 0.3
    top_p: float = 0.9
    system_prompt: str


class TrainingConfig(BaseModel):
    epochs: int
    batch_size: int
    learning_rate: float
    weight_decay: float
    max_seq_length: int
    validation_split: float


class BacktestConfig(BaseModel):
    initial_capital: float
    transaction_cost: float
    slippage: float


class RedisConfig(BaseModel):
    enabled: bool = False
    url: str = "redis://localhost:6379/0"


class Settings(BaseModel):
    app: AppSettings
    paths: Paths
    apis: APIConfig
    database: DatabaseConfig
    llm: LLMConfig
    training: TrainingConfig
    backtest: BacktestConfig
    redis: RedisConfig


_CONFIG_CACHE: Optional[Settings] = None


def load_config(path: Path | str = "config/config.yaml") -> Settings:
    global _CONFIG_CACHE
    if _CONFIG_CACHE:
        return _CONFIG_CACHE

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    settings = Settings(**raw)

    # ensure directories exist
    settings.paths.raw_data.mkdir(parents=True, exist_ok=True)
    settings.paths.processed_data.mkdir(parents=True, exist_ok=True)
    settings.paths.database.parent.mkdir(parents=True, exist_ok=True)

    _CONFIG_CACHE = settings
    return settings
