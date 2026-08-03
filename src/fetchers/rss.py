import aiohttp
import feedparser
from datetime import datetime, timezone
from .base import BaseFetcher, Article


REQUEST_HEADERS = {
    "User-Agent": (
        "HorizonAI-NewsRadar/0.1 "
        "(+https://github.com/jechreal-hub/horizon-ai-news-radar)"
    )
}


class RSSFetcher(BaseFetcher):
    def __init__(self, name: str, url: str):
        self._name = name
        self._url = url

    @property
    def source_name(self) -> str:
        return self._name

    async def fetch(self) -> list[Article]:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(headers=REQUEST_HEADERS, timeout=timeout) as session:
            async with session.get(self._url, allow_redirects=True) as response:
                response.raise_for_status()
                body = await response.read()

        feed = feedparser.parse(body)
        if feed.bozo and not feed.entries:
            raise ValueError(f"Invalid RSS/Atom feed: {feed.bozo_exception}")
        articles = []
        for entry in feed.entries[:20]:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            articles.append(Article(
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source=self._name,
                published_at=published,
                raw_content=entry.get("summary", ""),
            ))
        return articles
