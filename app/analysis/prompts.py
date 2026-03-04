"""All Claude prompts for the Trend Intelligence Agent."""
from __future__ import annotations

from datetime import date


def daily_digest_system() -> str:
    return """\
You are a senior cultural trend analyst and strategic advisor specialising in:
  - Non-alcoholic beverages and functional drinks
  - Hospitality and experience design
  - Consumer behaviour, identity, and social movements
  - Emerging subcultures and lifestyle shifts

Your role is to identify genuine cultural signals — not hype or noise — \
and translate them into actionable strategic intelligence for beverage brand builders.

Output must be structured, incisive, and concise. Every word must earn its place.
""".strip()


def daily_digest_user(articles_block: str, today: date) -> str:
    return f"""\
DATE: {today.isoformat()}

Below is a curated set of articles collected today from trend, culture, and industry sources.
Analyse them and produce the following structured intelligence report.

---
ARTICLES:
{articles_block}
---

Produce the report in EXACTLY this Markdown format:

## EXECUTIVE SUMMARY
(Maximum 300 words. What is the cultural moment today and why does it matter?)

## TREND SIGNALS

(Identify 6 to 12 distinct signals. Use this exact format for each:)

### SIGNAL [N]: [Short Title]

**What happened:** (1–3 sentences)

**Why it is a signal:** (What shift does this represent?)

**Societal layer:** (identity / control / mental health / community / pleasure / belonging / rebellion / status / spirituality)

**Implication for non-alcoholic beverages / hospitality:** (Concrete strategic implication)

**What to monitor:** (Specific indicators or communities to watch)

---

## TOP 3 EXPERIMENTS

### Experiment 1: [Title]
**Hypothesis:** ...
**Method:** ...
**Success metric:** ...

### Experiment 2: [Title]
**Hypothesis:** ...
**Method:** ...
**Success metric:** ...

### Experiment 3: [Title]
**Hypothesis:** ...
**Method:** ...
**Success metric:** ...
""".strip()


def build_articles_block(articles: list[dict], max_chars: int = 60_000) -> str:
    parts = []
    total = 0
    for i, art in enumerate(articles, 1):
        chunk = (
            f"--- Article {i} ---\n"
            f"[{art['source']} | {art['published_at'][:10]}] {art['title']}\n"
            f"{art['url']}\n"
            f"{art['clean_content']}\n\n"
        )
        if total + len(chunk) > max_chars:
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n".join(parts)
