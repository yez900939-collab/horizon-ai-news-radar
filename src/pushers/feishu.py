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
from src.llm.classifier import classify_by_keywords
from .base import BasePusher


SECURITY_CATEGORIES = {"AI 安全", "漏洞与威胁", "安全研究"}
SECURITY_SOURCES = {
    "cisa_advisories",
    "microsoft_security",
    "krebsonsecurity",
    "sans_isc",
}


class FeishuPusher(BasePusher):
    """Push the selected daily digest through a Feishu custom-bot webhook."""

    def __init__(
        self,
        webhook_url: str | None = None,
        signing_secret: str | None = None,
        include_security: bool = True,
    ):
        self.webhook_url = webhook_url or settings.feishu_webhook_url
        self.signing_secret = (
            settings.feishu_signing_secret
            if webhook_url is None and signing_secret is None
            else signing_secret
        )
        self.include_security = include_security

    @staticmethod
    def generate_signature(secret: str, timestamp: int) -> str:
        signing_key = f"{timestamp}\n{secret}".encode("utf-8")
        digest = hmac.new(signing_key, digestmod=hashlib.sha256).digest()
        return base64.b64encode(digest).decode("utf-8")

    async def push(self, articles: list[Article]) -> bool:
        if not self.webhook_url:
            logger.warning("FEISHU_WEBHOOK_URL not set, skipping push")
            return False

        security_articles = []
        ai_articles = []
        for article in articles:
            target = security_articles if self.is_security(article) else ai_articles
            target.append(article)
        digests = [
            ("AI 精选", ai_articles),
        ]
        if self.include_security:
            digests.append(("网络安全精选", security_articles))
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for digest_title, digest_articles in digests:
                if not digest_articles:
                    continue
                payload = self.build_payload(digest_articles, digest_title)
                if self.signing_secret:
                    timestamp = int(time.time())
                    payload["timestamp"] = timestamp
                    payload["sign"] = self.generate_signature(
                        self.signing_secret,
                        timestamp,
                    )
                async with session.post(self.webhook_url, json=payload) as response:
                    response.raise_for_status()
                    result = await response.json()

                if result.get("code", result.get("StatusCode")) != 0:
                    logger.error(f"Feishu push failed for {digest_title}: {result}")
                    raise RuntimeError(
                        f"Feishu webhook rejected {digest_title}: "
                        f"code={result.get('code', result.get('StatusCode'))}, "
                        f"msg={result.get('msg', result.get('StatusMessage', 'unknown'))}"
                    )

        logger.info(
            "Pushed Feishu digests: "
            f"AI={min(len(ai_articles), 10)}, "
            f"security={min(len(security_articles), 10) if self.include_security else 'disabled'}"
        )
        return True

    @staticmethod
    def is_security(article: Article) -> bool:
        if article.source in SECURITY_SOURCES:
            return True
        category = classify_by_keywords(article.title, article.tags)
        return category in SECURITY_CATEGORIES

    @staticmethod
    def build_payload(articles: list[Article], digest_title: str = "AI 精选") -> dict:
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
                        "title": f"🪐 Horizon {digest_title} · {today}",
                        "content": paragraphs,
                    }
                }
            },
        }
