from __future__ import annotations

import datetime as dt
from typing import List, Optional

import backoff
import httpx
from bs4 import BeautifulSoup
from loguru import logger

from src.utils.cache import TTLCache
from src.utils.config import Settings


class NewsArticle(dict):
    def __init__(self, *, title: str, url: str, published_at: str, source: str, summary: str):
        super().__init__(title=title, url=url, published_at=published_at, source=source, summary=summary)


class NewsScraper:
    def __init__(self, config: Settings, cache: Optional[TTLCache] = None):
        self.config = config
        self.cache = cache or TTLCache(config.app.cache_ttl_seconds)
        self.client = httpx.Client(timeout=10)

    @backoff.on_exception(backoff.expo, Exception, max_time=60)
    def fetch_news(self, symbol: str, days: int = 3, force_refresh: bool = False) -> List[NewsArticle]:
        cache_key = f"news:{symbol}:{days}"
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return [NewsArticle(**item) for item in cached]

        if self.config.apis.news_api.enabled and self.config.apis.news_api.api_key:
            articles = self._fetch_newsapi(symbol, days)
        else:
            articles = self._scrape_rss(symbol, days)

        self.cache.set(cache_key, articles)
        return [NewsArticle(**a) for a in articles]

    def _fetch_newsapi(self, symbol: str, days: int) -> List[dict]:
        endpoint = "https://newsapi.org/v2/everything"
        since = (dt.datetime.utcnow() - dt.timedelta(days=days)).isoformat()
        params = {
            "q": symbol,
            "from": since,
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": self.config.apis.news_api.api_key,
            "pageSize": 50,
        }
        try:
            resp = self.client.get(endpoint, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # network or quota issues
            logger.warning(f"NewsAPI failed ({exc}); continuing without news.")
            return []
        articles = []
        for item in data.get("articles", []):
            articles.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "published_at": item.get("publishedAt"),
                    "source": item.get("source", {}).get("name", "newsapi"),
                    "summary": item.get("description", ""),
                }
            )
        logger.info(f"Fetched {len(articles)} articles via NewsAPI for {symbol}")
        return articles

    def _scrape_rss(self, symbol: str, days: int) -> List[dict]:
        # fallback: use Reuters symbol news feed
        url = f"https://feeds.reuters.com/reuters/companyNews?symbol={symbol}.O"
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning(f"RSS fetch failed ({exc}); returning no news.")
            return []
        soup = BeautifulSoup(resp.text, "xml")
        cutoff = dt.datetime.utcnow() - dt.timedelta(days=days)
        articles = []
        for item in soup.find_all("item"):
            pub_date = item.pubDate.text if item.pubDate else ""
            try:
                parsed_date = dt.datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None)
            except Exception:
                parsed_date = cutoff
            if parsed_date < cutoff:
                continue
            articles.append(
                {
                    "title": item.title.text if item.title else "",
                    "url": item.link.text if item.link else "",
                    "published_at": parsed_date.isoformat(),
                    "source": "Reuters",
                    "summary": item.description.text if item.description else "",
                }
            )
        logger.info(f"Scraped {len(articles)} Reuters items for {symbol}")
        return articles
