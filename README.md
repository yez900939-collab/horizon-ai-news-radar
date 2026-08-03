# 🪐 Horizon AI 新闻雷达

> 定时抓取 AI 与网络安全资讯 → DeepSeek 智能摘要 → 飞书实时推送 → 生成日报与原始归档

当前源覆盖 AI 实验室/媒体，以及 CISA、Microsoft Security、Krebs、SANS 等安全情报。

## 快速开始

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 DeepSeek API Key

# 2. 安装依赖
uv sync

# 3. 运行
uv run python -m src.main fetch    # 只抓取
uv run python -m src.main run      # 完整流水线
uv run python -m src.main schedule # 定时调度
```

没有配置 `DEEPSEEK_API_KEY` 时，`fetch` 和 `run` 仍可工作，但日报不会包含 LLM 摘要。

## 配置

| 变量 | 用途 | 必需 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | DeepSeek 摘要 | 完整流水线必需 |
| `OPENAI_BASE_URL` | OpenAI-compatible API 地址 | 否，默认 DeepSeek |
| `LLM_MODEL` | 模型名 | 否，默认 `deepseek-v4-flash` |
| `FEISHU_WEBHOOK_URL` | 飞书群自定义机器人推送 | 否 |

本地密钥只写入被 Git 忽略的 `.env`。GitHub Actions 部署时，把同名变量写入仓库的
**Settings → Secrets and variables → Actions**，不要提交到代码。

定时任务使用 UTC `00:00 / 04:00 / 10:00`，对应北京时间 `08:00 / 12:00 / 18:00`。

每次运行会同时生成：

- `data/reports/YYYY-MM-DD.md`：中文日报。
- `data/raw/YYYY-MM-DD/HHMMSS.json`：未经清洗的原始 RSS/Atom 条目，随日报提交到 GitHub。
- 飞书富文本消息：实时推送优先级最高的 10 条资讯。

## 结构

```
src/
  fetchers/    # 数据源采集
  cleaners/    # 清洗管道
  llm/         # LLM 摘要/分类
  pushers/     # 推送通道
  daily/       # 日报生成
  storage/     # 数据存储
  scheduler.py # 定时调度
  config.py    # 配置管理
  main.py      # CLI 入口
```

## 技术栈

- Python 3.12+ / uv
- aiohttp / feedparser / BeautifulSoup
- OpenAI SDK / pydantic-settings
- APScheduler / SQLAlchemy + aiosqlite
- Jinja2 / loguru
