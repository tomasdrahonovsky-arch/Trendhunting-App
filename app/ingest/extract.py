"""Extract and clean article content from raw HTML."""
from __future__ import annotations

import hashlib
import logging
import re
import unicodedata

from bs4 import BeautifulSoup
from readability import Document

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_readable(html: str, url: str = "") -> tuple[str, str]:
    """Returns (title, clean_text)."""
    try:
        doc = Document(html)
        title = clean_text(doc.title() or "")
        summary_html = doc.summary(html_partial=True)
        soup = BeautifulSoup(summary_html, "lxml")
        body_text = clean_text(soup.get_text(separator=" "))
        return title, body_text
    except Exception as exc:
        logger.warning("readability failed for %s: %s", url, exc)
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        title = clean_text(soup.title.string if soup.title else "")
        body_text = clean_text(soup.get_text(separator=" "))
        return title, body_text


def content_hash(text: str) -> str:
    normalised = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.sha256(normalised.encode()).hexdigest()
