"""
Main pipeline for GitHub Actions deployment.

Storage: flat JSON files committed to the repo (no database needed).
  - data/seen_hashes.json    → deduplication across runs
  - docs/YYYY-MM-DD.html     → daily newsletters (served via GitHub Pages)
  - docs/index.html          → homepage listing all issues
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from app.analysis.claude import call_claude
from app.analysis.prompts import build_articles_block, daily_digest_system, daily_digest_user
from app.ingest.rss import ingest_source
from app.publish.render_html import render

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent
SOURCES_FILE = BASE / "config" / "sources.yaml"
DATA_DIR = BASE / "data"
DOCS_DIR = BASE / "docs"
HASHES_FILE = DATA_DIR / "seen_hashes.json"

DATA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)


# ── Hash store (deduplication) ────────────────────────────────────────────────

def load_hashes() -> set[str]:
    if HASHES_FILE.exists():
        return set(json.loads(HASHES_FILE.read_text()))
    return set()


def save_hashes(hashes: set[str]) -> None:
    # Keep only the last 5000 hashes to avoid unbounded growth
    recent = list(hashes)[-5000:]
    HASHES_FILE.write_text(json.dumps(recent, indent=2))


# ── Index page ────────────────────────────────────────────────────────────────

def rebuild_index() -> None:
    issues = sorted(DOCS_DIR.glob("????-??-??.html"), reverse=True)
    items = ""
    for f in issues:
        d = f.stem  # e.g. 2025-01-15
        try:
            label = datetime.strptime(d, "%Y-%m-%d").strftime("%A, %B %d, %Y")
        except ValueError:
            label = d
        items += f'    <li><a href="{f.name}">{label}</a></li>\n'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Trend Intelligence Daily</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      max-width: 600px; margin: 60px auto; padding: 0 24px;
      background: #f5f4f0; color: #1a1a1a; line-height: 1.6;
    }}
    h1 {{ font-size: 26px; font-weight: 800; margin-bottom: 6px; }}
    .sub {{ color: #888; font-size: 14px; margin-bottom: 40px; }}
    ul {{ list-style: none; padding: 0; }}
    li {{ margin-bottom: 12px; }}
    a {{
      font-size: 16px; color: #0055cc; text-decoration: none;
      padding: 10px 16px; display: block;
      background: white; border-radius: 6px;
      border: 1px solid #e0e0e0;
    }}
    a:hover {{ background: #eef4ff; border-color: #0055cc; }}
    .empty {{ color: #aaa; font-style: italic; }}
  </style>
</head>
<body>
  <h1>Trend Intelligence Daily</h1>
  <p class="sub">Daily cultural signals for non-alcoholic beverages &amp; hospitality.</p>
  <ul>
{items if items else '    <li class="empty">No issues yet. First run coming soon.</li>'}
  </ul>
</body>
</html>"""

    (DOCS_DIR / "index.html").write_text(html)
    logger.info("Index rebuilt with %d issues", len(issues))


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run() -> None:
    today = date.today()
    logger.info("=== Trend Intelligence Agent — %s ===", today)

    # Load sources
    sources_data = yaml.safe_load(SOURCES_FILE.read_text())
    sources = sources_data.get("sources", [])
    logger.info("Loaded %d sources", len(sources))

    # Load seen hashes for deduplication
    seen_hashes = load_hashes()
    logger.info("Loaded %d known hashes", len(seen_hashes))

    # Ingest all sources
    all_articles: list[dict] = []
    for source in sources:
        try:
            articles = ingest_source(source, seen_hashes)
            all_articles.extend(articles)
        except Exception as exc:
            logger.error("Source %s failed: %s", source["name"], exc)

    logger.info("Total new articles: %d", len(all_articles))

    if not all_articles:
        logger.warning("No new articles today — skipping analysis")
        # Still rebuild index in case this is a fresh deploy
        rebuild_index()
        return

    # Save updated hashes
    new_hashes = {a["hash"] for a in all_articles}
    save_hashes(seen_hashes | new_hashes)

    # Build prompt and call Claude
    articles_block = build_articles_block(all_articles)
    system = daily_digest_system()
    user = daily_digest_user(articles_block, today)

    logger.info("Calling Claude for analysis...")
    response = call_claude(system=system, user=user, max_tokens=5000)

    # Render HTML
    html = render(
        markdown=response.content,
        target_date=today,
        article_count=len(all_articles),
    )

    # Write newsletter file
    output_path = DOCS_DIR / f"{today.isoformat()}.html"
    output_path.write_text(html, encoding="utf-8")
    logger.info("Newsletter written: %s", output_path)

    # Also save raw markdown for reference
    md_path = DATA_DIR / f"{today.isoformat()}.md"
    md_path.write_text(response.content, encoding="utf-8")

    # Rebuild index
    rebuild_index()

    logger.info(
        "Done — tokens: %d in / %d out",
        response.input_tokens,
        response.output_tokens,
    )


if __name__ == "__main__":
    run()
