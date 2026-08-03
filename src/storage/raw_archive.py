import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from loguru import logger

from src.fetchers.base import Article


class RawArchive:
    def __init__(self, archive_dir: Path = Path("data/raw")):
        self.archive_dir = archive_dir

    def save(self, articles: list[Article], now: datetime | None = None) -> Path:
        archived_at = now or datetime.now(ZoneInfo("Asia/Shanghai"))
        target_dir = self.archive_dir / archived_at.strftime("%Y-%m-%d")
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{archived_at.strftime('%H%M%S')}.json"

        payload = {
            "archived_at": archived_at.isoformat(),
            "article_count": len(articles),
            "articles": [self._serialize(article) for article in articles],
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(f"Raw archive saved to {path}")
        return path

    @staticmethod
    def _serialize(article: Article) -> dict:
        return {
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "published_at": (
                article.published_at.isoformat() if article.published_at else None
            ),
            "raw_content": article.raw_content,
        }
