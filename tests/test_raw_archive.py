import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.fetchers.base import Article
from src.storage.raw_archive import RawArchive


class RawArchiveTests(unittest.TestCase):
    def test_saves_original_articles_in_timestamped_json(self):
        article = Article(
            title="Security bulletin",
            url="https://example.com/security",
            source="example",
            published_at=datetime(2026, 8, 3, 1, 2, tzinfo=timezone.utc),
            raw_content="<p>Original feed body</p>",
        )
        archive_time = datetime(2026, 8, 3, 8, 30, 45, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmp:
            path = RawArchive(Path(tmp)).save([article], now=archive_time)
            payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(path.name, "083045.json")
        self.assertEqual(path.parent.name, "2026-08-03")
        self.assertEqual(payload["article_count"], 1)
        self.assertEqual(payload["articles"][0]["raw_content"], "<p>Original feed body</p>")
        self.assertEqual(payload["articles"][0]["published_at"], "2026-08-03T01:02:00+00:00")


if __name__ == "__main__":
    unittest.main()
