from __future__ import annotations

import datetime as dt
from typing import List, Optional

import backoff
from loguru import logger

try:
    import tweepy  # type: ignore
except ImportError:
    tweepy = None

try:
    import praw  # type: ignore
except ImportError:
    praw = None

from src.utils.cache import TTLCache
from src.utils.config import Settings


class SocialPost(dict):
    def __init__(self, *, text: str, author: str, source: str, created_at: str, url: str):
        super().__init__(text=text, author=author, source=source, created_at=created_at, url=url)


class SocialCollector:
    def __init__(self, config: Settings, cache: Optional[TTLCache] = None):
        self.config = config
        self.cache = cache or TTLCache(config.app.cache_ttl_seconds)

    @backoff.on_exception(backoff.expo, Exception, max_time=60)
    def fetch(self, symbol: str, limit: int = 50, force_refresh: bool = False) -> List[SocialPost]:
        cache_key = f"social:{symbol}:{limit}"
        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return [SocialPost(**p) for p in cached]

        posts: List[dict] = []
        posts.extend(self._fetch_twitter(symbol, limit))
        posts.extend(self._fetch_reddit(symbol, limit))
        logger.info(f"Collected {len(posts)} social posts for {symbol}")
        self.cache.set(cache_key, posts)
        return [SocialPost(**p) for p in posts]

    def _fetch_twitter(self, symbol: str, limit: int) -> List[dict]:
        if not (self.config.apis.twitter.enabled and tweepy and self.config.apis.twitter.bearer_token):
            return []
        client = tweepy.Client(bearer_token=self.config.apis.twitter.bearer_token)
        query = f"${symbol} (lang:en) -is:retweet"
        tweets = client.search_recent_tweets(query=query, max_results=min(limit, 100))
        results = []
        for tw in tweets.data or []:
            created = tw.created_at or dt.datetime.utcnow()
            results.append(
                {
                    "text": tw.text,
                    "author": str(tw.author_id),
                    "source": "twitter",
                    "created_at": created.isoformat(),
                    "url": f"https://twitter.com/i/web/status/{tw.id}",
                }
            )
        return results

    def _fetch_reddit(self, symbol: str, limit: int) -> List[dict]:
        if not (self.config.apis.reddit.enabled and praw):
            return []
        reddit = praw.Reddit(
            client_id=self.config.apis.reddit.client_id,
            client_secret=self.config.apis.reddit.client_secret,
            user_agent=self.config.apis.reddit.user_agent,
        )
        subreddit = reddit.subreddit("wallstreetbets")
        results = []
        for post in subreddit.search(query=symbol, limit=limit, syntax="lucene"):
            created = dt.datetime.fromtimestamp(post.created_utc)
            results.append(
                {
                    "text": post.title,
                    "author": post.author.name if post.author else "",
                    "source": "reddit",
                    "created_at": created.isoformat(),
                    "url": post.url,
                }
            )
        return results
