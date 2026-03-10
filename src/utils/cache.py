from __future__ import annotations

import json
import time
from typing import Any, Optional

try:
    import redis  # type: ignore
except ImportError:  # redis optional
    redis = None


class TTLCache:
    def __init__(self, ttl_seconds: int, redis_url: Optional[str] = None):
        self.ttl = ttl_seconds
        self.mem_store: dict[str, tuple[float, Any]] = {}
        self.client = redis.Redis.from_url(redis_url) if redis_url and redis else None

    def get(self, key: str) -> Optional[Any]:
        if self.client:
            val = self.client.get(key)
            return json.loads(val) if val else None
        now = time.time()
        value = self.mem_store.get(key)
        if not value:
            return None
        expires, data = value
        if now > expires:
            self.mem_store.pop(key, None)
            return None
        return data

    def set(self, key: str, value: Any) -> None:
        if self.client:
            self.client.setex(key, self.ttl, json.dumps(value))
            return
        self.mem_store[key] = (time.time() + self.ttl, value)
