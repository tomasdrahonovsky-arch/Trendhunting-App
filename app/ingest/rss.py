"""RSS feed ingestion via feedparser."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from app.ingest.extract import clean_text, content_hash, extract_readable

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; TrendAgent/1.0)"
}


def _parse_date(entry: Any) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def _fetch_url(url: str) -> str:
    try:
        with httpx.Client(follow_redirects=True, timeout=20, headers=_HEADERS) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception:
        return ""


def ingest_source(source: dict[str, Any], seen_hashes: set[str]) -> list[dict[str, Any]]:
    """
    Ingest one RSS source.
    Returns list of new article dicts.
    """
    url: str = source["url"]
    tags: list[str] = source.get("tags") or []
    source_name: str = source["name"]

    logger.info("Fetching: %s", source_name)

    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        logger.error("feedparser error for %s: %s", url, exc)
        return []

    articles = []
    for entry in feed.entries[:20]:  # cap per source
        article_url = getattr(entry, "link", None) or getattr(entry, "id", None)
        if not article_url:
            continue

        raw_html = ""
        if hasattr(entry, "content") and entry.content:
            raw_html = entry.content[0].get("value", "")
        if not raw_html and hasattr(entry, "summary"):
            raw_html = entry.summary or ""
        if len(raw_html.strip()) < 100:
            raw_html = _fetch_url(article_url)

        title, clean = extract_readable(raw_html, article_url)
        if not title:
            title = clean_text(getattr(entry, "title", "") or "")
        if len(clean) < 100:
            continue

        chash = content_hash(clean)
        if chash in seen_hashes:
            continue

        seen_hashes.add(chash)
        articles.append({
            "source": source_name,
            "url": article_url,
            "title": title,
            "published_at": _parse_date(entry),
            "clean_content": clean[:2000],  # cap storage per article
            "tags": tags,
            "hash": chash,
        })

    logger.info("  %s → %d new articles", source_name, len(articles))
    return articles
