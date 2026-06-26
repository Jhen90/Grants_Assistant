# ============================================================
# File: src/utils/export.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Export utilities — Markdown → HTML → PDF pipeline via weasyprint
# ============================================================

from __future__ import annotations

from pathlib import Path

from src.utils.logger import get_logger

log = get_logger(__name__)


def markdown_to_pdf(markdown_text: str, output_path: Path, title: str = "GMAS Export") -> Path:
    """
    Convert Markdown text to a PDF file at output_path.
    Requires: weasyprint (conda-forge) + markdown package.
    """
    html = markdown_to_html(markdown_text, title=title)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise ImportError(
            "weasyprint is not available. Install via: conda install -c conda-forge weasyprint"
        ) from exc

    HTML(string=html).write_pdf(str(output_path))
    log.info("PDF written: %s", output_path)
    return output_path


def markdown_to_html(markdown_text: str, title: str = "GMAS Export") -> str:
    """Convert Markdown text to a complete, print-ready HTML document string."""
    try:
        import markdown as md_lib
        body = md_lib.markdown(
            markdown_text,
            extensions=["tables", "toc", "fenced_code"],
        )
    except ImportError:
        log.warning("markdown package not installed — rendering as preformatted text.")
        body = f"<pre>{markdown_text}</pre>"

    return _html_wrapper(body, title)


def markdown_to_file(markdown_text: str, output_path: Path) -> Path:
    """Write raw Markdown text to a .md file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown_text, encoding="utf-8")
    log.info("Markdown written: %s", output_path)
    return output_path


def _html_wrapper(body: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: "Segoe UI", Arial, sans-serif;
      font-size: 11pt;
      color: #1a1a1a;
      margin: 0;
      padding: 0;
    }}
    .page-wrap {{ max-width: 7.5in; margin: 0 auto; padding: 0.75in; }}
    h1 {{
      font-size: 20pt;
      border-bottom: 2px solid #2c5282;
      padding-bottom: 8px;
      color: #1a365d;
    }}
    h2 {{
      font-size: 14pt;
      color: #2c5282;
      margin-top: 20pt;
      border-left: 4px solid #4299e1;
      padding-left: 8px;
    }}
    h3 {{ font-size: 12pt; color: #444; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 10px 0 16px;
      font-size: 10pt;
    }}
    th {{
      background: #ebf8ff;
      color: #2c5282;
      padding: 6px 10px;
      text-align: left;
      border: 1px solid #bee3f8;
    }}
    td {{
      padding: 5px 10px;
      border: 1px solid #e2e8f0;
    }}
    tr:nth-child(even) td {{ background: #f7fafc; }}
    blockquote {{
      border-left: 4px solid #f6e05e;
      background: #fffbeb;
      margin: 12px 0;
      padding: 8px 16px;
      font-style: italic;
    }}
    code {{ font-family: monospace; background: #f0f0f0; padding: 2px 4px; }}
    pre code {{ display: block; padding: 8px; }}
    hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 20px 0; }}
    @page {{
      size: letter;
      margin: 0.75in;
    }}
    @media print {{
      .page-wrap {{ padding: 0; }}
    }}
  </style>
</head>
<body>
  <div class="page-wrap">
{body}
  </div>
</body>
</html>"""
