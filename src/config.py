from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # OpenAI-compatible LLM
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    openai_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-v4-flash"

    # Push channels
    wecom_webhook_url: Optional[str] = None
    feishu_webhook_url: Optional[str] = None
    feishu_signing_secret: Optional[str] = None

    # Behavior
    max_articles_per_fetch: int = 50
    dedup_days: int = 3
    report_retention_days: int = 30

    # Database
    database_url: str = "sqlite+aiosqlite:///data/horizon.db"

    @property
    def llm_api_key(self) -> str:
        return self.deepseek_api_key or self.openai_api_key

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
