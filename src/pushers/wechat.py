import aiohttp
from src.config import settings
from src.fetchers.base import Article
from .base import BasePusher
from loguru import logger


class WeComPusher(BasePusher):
    """企业微信机器人推送"""

    async def push(self, articles: list[Article]) -> bool:
        if not settings.wecom_webhook_url:
            logger.warning("WECOM_WEBHOOK_URL not set, skipping push")
            return False
        content = "\n\n".join(
            f"**{a.title}**\n{a.summary or '暂无摘要'}\n[查看原文]({a.url})"
            for a in articles[:5]
        )
        payload = {"msgtype": "markdown", "markdown": {"content": content}}
        async with aiohttp.ClientSession() as session:
            async with session.post(settings.wecom_webhook_url, json=payload) as resp:
                result = await resp.json()
                if result.get("errcode") != 0:
                    logger.error(f"WeCom push failed: {result}")
                    return False
                logger.info(f"Pushed {len(articles)} articles to WeCom")
                return True
