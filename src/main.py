import asyncio
import sys
from copy import deepcopy
from loguru import logger
from src.config import settings
from src.fetchers.rss import RSSFetcher
from src.fetchers.sources import RSS_SOURCES
from src.cleaners.dedup import DedupPipeline
from src.cleaners.formatter import clean_content
from src.llm.summarizer import LLMSummarizer
from src.daily.report import DailyReport
from src.pushers.feishu import FeishuPusher
from src.storage.raw_archive import RawArchive


async def run_pipeline():
    logger.info("=== Pipeline started ===")

    # 1. Fetch
    fetchers = [RSSFetcher(name, url) for name, url in RSS_SOURCES.items()]
    all_articles = []
    for f in fetchers:
        try:
            articles = await f.fetch()
            logger.info(f"Fetched {len(articles)} from {f.source_name}")
            all_articles.extend(articles)
        except Exception as e:
            logger.error(f"Failed to fetch {f.source_name}: {e!r}")

    # Preserve the original feed payload before cleaning and summarization.
    RawArchive().save(all_articles)

    # 2. Clean & dedup
    dedup = DedupPipeline()
    clean_articles = []
    for a in all_articles:
        if not dedup.is_duplicate(a):
            a.raw_content = clean_content(a.raw_content)
            clean_articles.append(a)
    logger.info(f"After dedup: {len(clean_articles)} articles")

    # 3. LLM summarize
    if settings.llm_api_key:
        summarizer = LLMSummarizer()
        for a in clean_articles[:settings.max_articles_per_fetch]:
            result = await summarizer.summarize(a)
            if result:
                a.summary = result.get("summary", "")
                a.tags = result.get("tags", [])
                a.importance = result.get("importance", 3)
    else:
        logger.warning("LLM API key not set; generating a report without LLM summaries")

    # 4. Generate daily report
    report = DailyReport()
    content = report.generate(clean_articles)
    report.save(content)

    # 5. Push to configured channels
    if settings.feishu_webhook_url:
        await FeishuPusher().push(clean_articles)
    if settings.feishu_ai_webhook_url:
        ai_articles = [
            deepcopy(article)
            for article in clean_articles
            if not FeishuPusher.is_security(article)
        ]
        ai_summarizer = LLMSummarizer(api_key=settings.deepseek_ai_api_key)
        for article in ai_articles[:settings.max_articles_per_fetch]:
            result = await ai_summarizer.summarize(article)
            if result:
                article.summary = result.get("summary", "")
                article.tags = result.get("tags", [])
                article.importance = result.get("importance", 3)
        await FeishuPusher(
            webhook_url=settings.feishu_ai_webhook_url,
            signing_secret=None,
            include_security=False,
        ).push(ai_articles)

    logger.info(f"=== Pipeline done: {len(clean_articles)} articles processed ===")
    return clean_articles


async def cmd_fetch():
    """Only fetch, no LLM"""
    fetchers = [RSSFetcher(name, url) for name, url in RSS_SOURCES.items()]
    for f in fetchers:
        try:
            articles = await f.fetch()
            logger.info(f"{f.source_name}: {len(articles)} articles")
        except Exception as e:
            logger.error(f"{f.source_name}: fetch failed: {e!r}")


async def cmd_schedule():
    from src.scheduler import start_scheduler
    start_scheduler()
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "fetch":
        asyncio.run(cmd_fetch())
    elif cmd == "schedule":
        asyncio.run(cmd_schedule())
    elif cmd == "run":
        asyncio.run(run_pipeline())
    else:
        print(f"Usage: uv run python -m src.main [run|fetch|schedule]")


if __name__ == "__main__":
    main()
