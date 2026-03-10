from __future__ import annotations

import datetime as dt
import random
from typing import Dict, List

import feedparser
from loguru import logger


class NewsScraper:
    def __init__(self, config, cache=None):
        self.config = config
        self.cache = cache
        # Default working feeds
        self.working_feeds = [
            "http://feeds.reuters.com/reuters/businessNews",
            "http://feeds.reuters.com/reuters/companyNews",
            "https://moxie.foxbusiness.com/google-publisher/markets.xml",
            "https://seekingalpha.com/feed.xml",
            "https://www.investing.com/rss/news.rss",
            "https://www.marketwatch.com/feeds/topstories",
            # Indian financial news
            "https://economictimes.indiatimes.com/markets/rssfeeds",
            "https://www.moneycontrol.com/rss/latestnews.xml",
            "https://www.business-standard.com/rss/markets.rss",
        ]

    def fetch_news(self, symbol: str, days: int = 7, force_refresh: bool = False) -> List[Dict]:
        articles: List[Dict] = []
        since_date = dt.datetime.utcnow() - dt.timedelta(days=days)

        feeds = self.config.news_sources.rss_feeds if getattr(self.config, "news_sources", None) and self.config.news_sources.enabled else self.working_feeds
        logger.info(f"Searching {symbol} news from {len(feeds)} sources")

        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                if not feed.entries:
                    continue
                feed_name = feed.feed.get("title", feed_url)
                for entry in feed.entries[:15]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "") or entry.get("description", "")
                    if symbol.upper() not in (title + summary).upper():
                        continue
                    published = entry.get("published", "") or entry.get("updated", "")
                    try:
                        pub_dt = dt.datetime(*entry.published_parsed[:6]) if hasattr(entry, "published_parsed") else since_date
                    except Exception:
                        pub_dt = since_date
                    if pub_dt < since_date:
                        continue
                    articles.append(
                        {
                            "title": title,
                            "published": published or pub_dt.isoformat(),
                            "source": feed_name,
                            "summary": summary[:300] if summary else title,
                            "url": entry.get("link", ""),
                        }
                    )
            except Exception as exc:
                logger.debug(f"Feed {feed_url} error: {exc}")
                continue

        if not articles:
            logger.warning("No real news found; generating mock articles.")
            articles = self._generate_mock_news(symbol, days)

        logger.info(f"Total articles for {symbol}: {len(articles)}")
        return articles

    def _generate_mock_news(self, symbol: str, days: int) -> List[Dict]:
        mock_articles: List[Dict] = []
        sources = ["Bloomberg", "Reuters", "CNBC", "WSJ", "Financial Times"]
        templates = [
            f"{symbol} announces new product line, analysts raise price target",
            f"Earnings preview: {symbol} expected to beat estimates",
            f"{symbol} invests heavily in AI; market reacts",
            f"{symbol} faces regulatory review; shares volatile",
            f"{symbol} expands buyback program amid strong cash flows",
        ]
        for i in range(min(days, 10)):
            date = dt.datetime.utcnow() - dt.timedelta(days=i)
            for _ in range(random.randint(1, 2)):
                mock_articles.append(
                    {
                        "title": random.choice(templates),
                        "published": date.strftime("%Y-%m-%d %H:%M:%S"),
                        "source": random.choice(sources),
                        "summary": f"Mock article about {symbol} generated offline.",
                        "url": "https://example.com/mock-news",
                    }
                )
        return mock_articles
