import re


CATEGORIES = [
    "AI 安全",       # AI/LLM security
    "漏洞与威胁",    # Vulnerabilities and active threats
    "安全研究",      # Security research and threat intelligence
    "重磅发布",     # Major releases
    "行业动态",     # Industry news
    "工具 & 开源",  # Tools & OSS
    "融资 & 商业",  # Funding & Business
    "研究 & 论文",  # Research & Papers
]


def _contains_any(text: str, terms: list[str]) -> bool:
    for term in terms:
        if re.fullmatch(r"[a-z0-9-]+", term):
            pattern = rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])"
            if re.search(pattern, text):
                return True
        elif term in text:
            return True
    return False


def classify_by_keywords(title: str, tags: list[str]) -> str:
    title_lower = title.lower()
    text = title_lower + " " + " ".join(tags).lower()
    ai_terms = ["ai", "llm", "model", "prompt", "jailbreak", "人工智能", "大模型"]
    security_terms = [
        "security", "prompt injection", "jailbreak", "red team", "安全", "越狱",
    ]
    if _contains_any(text, ai_terms) and _contains_any(text, security_terms):
        return "AI 安全"
    if _contains_any(text, [
        "cve", "vulnerability", "exploit", "rce", "zero-day", "0-day",
        "malware", "ransomware", "breach", "漏洞", "利用", "勒索", "入侵",
    ]):
        return "漏洞与威胁"
    if _contains_any(text, [
        "threat intelligence", "incident response", "forensics", "apt",
        "security research", "威胁情报", "应急响应", "取证", "安全研究",
    ]):
        return "安全研究"
    if any(kw in text for kw in ["release", "launch", "announce", "发布", "announcing"]):
        return "重磅发布"
    if any(kw in text for kw in ["funding", "融资", "acquisition", "收购", "商业"]):
        return "融资 & 商业"
    if any(kw in text for kw in ["open source", "github", "开源", "tool", "library"]):
        return "工具 & 开源"
    if any(kw in text for kw in ["paper", "research", "study", "研究", "arxiv"]):
        return "研究 & 论文"
    return "行业动态"
