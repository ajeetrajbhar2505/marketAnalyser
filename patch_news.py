# Save this as patch_news.py and run: python patch_news.py
import asyncio
from src.data_collection.news_scraper import NewsScraper

# Monkey patch the fetch_news method
async def mock_fetch_news(self, symbol, days=7):
    """Return mock news when real fetching fails"""
    mock_articles = [
        {
            'title': f"{symbol} announces breakthrough in AI technology",
            'published': '2026-03-10',
            'source': 'Mock News',
            'summary': f"Analysts raise price target for {symbol}"
        },
        {
            'title': f"Earnings preview: {symbol} expected to beat estimates",
            'published': '2026-03-09',
            'source': 'Mock News', 
            'summary': f"Strong iPhone sales driving growth"
        },
        {
            'title': f"Market sentiment turns bullish for tech stocks",
            'published': '2026-03-08',
            'source': 'Mock News',
            'summary': f"{symbol} leading the rally"
        }
    ]
    print(f"✅ Generated {len(mock_articles)} mock articles for {symbol}")
    return mock_articles

# Apply the patch
NewsScraper.fetch_news = mock_fetch_news

# Now run your main script
print("🎭 Mock news data enabled! Run your prediction now.")