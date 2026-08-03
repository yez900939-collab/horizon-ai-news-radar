import base64
import hashlib
import hmac
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import aiohttp
from loguru import logger

from src.config import settings
from src.fetchers.base import Article
from .base import BasePusher


class FeishuPusher(BasePusher):
    """Push the selected daily digest through a Feishu custom-bot webhook."""

    def __init__(
        self,
        webhook_url: str | None = None,
        signing_secret: str | None = None,
    ):
        self.webhook_url = webhook_url or settings.feishu_webhook_url
        self.signing_secret = signing_secret or settings.feishu_signing_secret

    @staticmethod
    def generate_signature(secret: str, timestamp: int) -> str:
        signing_key = f"{timestamp}\n{secret}".encode("utf-8")
        digest = hmac.new(signing_key, digestmod=hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    async def push(self, articles: list[Article]) -> bool:
        if not self.webhook_url:
            logger.warning("FEISHU_WEBHOOK_URL not set, skipping push")
            return False

        payload = self.build_payload(articles)
        if self.signing_secret:
            timestamp = int(time.time())
            payload["timestamp"] = timestamp
            payload["sign"] = self.generate_signature(
                self.signing_secret,
                timestamp,
            )
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.webhook_url, json=payload) as response:
                response.raise_for_status()
                result = await response.json()

        if result.get("code", result.get("StatusCode")) != 0:
            logger.error(f"Feishu push failed: {result}")
            raise RuntimeError(
                f"Feishu webhook rejected the message: "
                f"code={result.get('code', result.get('StatusCode'))}, "
                f"msg={result.get('msg', result.get('StatusMessage', 'unknown'))}"
            )

        logger.info(f"Pushed {min(len(articles), 10)} articles to Feishu")
        return True

    @staticmethod
    def build_payload(articles: list[Article]) -> dict:
        selected = sorted(
            articles,
            key=lambda article: article.importance,
            reverse=True,
        )[:10]
        today = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")
        paragraphs = [[{
            "tag": "text",
            "text": f"本次共处理 {len(articles)} 篇资讯，以下为优先级最高的 {len(selected)} 篇：",
        }]]

        for article in selected:
            title = article.title.strip()[:120] or "未命名资讯"
            summary = article.summary.strip()[:160] or "暂无 LLM 摘要"
            paragraphs.append([
                {"tag": "a", "text": f"⭐{article.importance} {title}", "href": article.url},
                {"tag": "text", "text": f"\n{summary}（{article.source}）"},
            ])

        return {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": f"🪐 Horizon AI 日报 · {today}",
                        "content": paragraphs,
                    }
                }
            },
        }
