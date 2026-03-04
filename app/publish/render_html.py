"""Render a clean HTML newsletter from Markdown."""
from __future__ import annotations

import re
from datetime import date


def md_to_html(md: str) -> str:
    lines = md.split("\n")
    html_lines: list[str] = []
    in_ul = False

    for line in lines:
        if line.startswith("### "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            html_lines.append(f"<h3>{_inline(line[4:])}</h3>")
        elif line.startswith("## "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            html_lines.append(f"<h2>{_inline(line[3:])}</h2>")
        elif line.startswith("# "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            html_lines.append(f"<h1>{_inline(line[2:])}</h1>")
        elif line.strip() in ("---", "***"):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            html_lines.append("<hr>")
        elif line.startswith("- ") or line.startswith("* "):
            if not in_ul:
                html_lines.append("<ul>"); in_ul = True
            html_lines.append(f"<li>{_inline(line[2:])}</li>")
        elif not line.strip():
            if in_ul: html_lines.append("</ul>"); in_ul = False
            html_lines.append("")
        else:
            if in_ul: html_lines.append("</ul>"); in_ul = False
            html_lines.append(f"<p>{_inline(line)}</p>")

    if in_ul:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def _inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
    return text


def render(markdown: str, target_date: date, article_count: int) -> str:
    body_html = md_to_html(markdown)
    date_str = target_date.strftime("%A, %B %d, %Y")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Trend Intelligence — {date_str}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
      background: #f5f4f0;
      color: #1a1a1a;
      line-height: 1.65;
    }}
    .wrapper {{ max-width: 700px; margin: 40px auto; padding: 0 24px 80px; }}
    .header {{
      border-top: 5px solid #1a1a1a;
      padding-top: 28px;
      margin-bottom: 40px;
    }}
    .header .eyebrow {{
      font-size: 11px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: #888;
      margin-bottom: 8px;
    }}
    .header h1 {{
      font-size: 28px;
      font-weight: 800;
      letter-spacing: -0.5px;
      line-height: 1.2;
    }}
    .header .meta {{
      font-size: 13px;
      color: #999;
      margin-top: 8px;
    }}
    .content h2 {{
      font-size: 20px;
      font-weight: 700;
      margin: 40px 0 12px;
      padding-bottom: 8px;
      border-bottom: 2px solid #e8e8e8;
      color: #111;
    }}
    .content h3 {{
      font-size: 16px;
      font-weight: 700;
      margin: 28px 0 10px;
      color: #222;
      background: #eee;
      padding: 8px 12px;
      border-radius: 4px;
    }}
    .content p {{
      margin-bottom: 14px;
      font-size: 15.5px;
      color: #2a2a2a;
    }}
    .content ul {{
      margin: 8px 0 16px 24px;
    }}
    .content li {{
      margin-bottom: 6px;
      font-size: 15px;
    }}
    .content strong {{ font-weight: 700; color: #111; }}
    .content em {{ font-style: italic; color: #555; }}
    .content a {{ color: #0055cc; text-decoration: none; }}
    .content a:hover {{ text-decoration: underline; }}
    .content hr {{
      border: none;
      border-top: 1px solid #ddd;
      margin: 32px 0;
    }}
    .footer {{
      margin-top: 60px;
      padding-top: 20px;
      border-top: 1px solid #ddd;
      font-size: 12px;
      color: #aaa;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="eyebrow">Trend Intelligence Daily</div>
      <h1>{date_str}</h1>
      <div class="meta">{article_count} articles analysed across beverages, culture &amp; society</div>
    </div>
    <div class="content">
      {body_html}
    </div>
    <div class="footer">
      Generated automatically by Trend Intelligence Agent
    </div>
  </div>
</body>
</html>"""
