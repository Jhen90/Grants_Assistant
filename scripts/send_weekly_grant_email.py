# ============================================================
# File: scripts/send_weekly_grant_email.py
# Version: 1.0.0
# Created: 2026-08-17
# Modified: 2026-08-17
# Description: Weekly grant email. Runs the discovery scan, takes the top-ranked
#   candidates awaiting review, and emails them (title, agency, deadline, apply
#   link) via Gmail SMTP. Designed to be run by GitHub Actions on a schedule.
#
#   Credentials come from the environment — never hard-code them:
#     GMAIL_USER          sender address (e.g. dojoatsomernova@gmail.com)
#     GMAIL_APP_PASSWORD  Gmail app password (GitHub Actions secret)
#     EMAIL_TO            comma-separated recipient list
#
#   Usage:
#     python -m scripts.send_weekly_grant_email
#     python -m scripts.send_weekly_grant_email --dry-run   # print, don't send
# ============================================================

from __future__ import annotations

import argparse
import os
import smtplib
import sys
from datetime import date
from email.message import EmailMessage
from html import escape

from scripts.run_discovery_scan import DEFAULT_QUERIES
from src.db.database import get_db, init_db
from src.services.discovery_service import DiscoveryService
from src.services.scout_report_service import ScoutReportService
from src.utils.logger import get_logger

log = get_logger("weekly_grant_email")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587  # STARTTLS
DEFAULT_LIMIT = 25

_NO_LINK = "(no link)"


# ── recipients ─────────────────────────────────────────────────────────────────


def parse_recipients(raw: str) -> list[str]:
    """Split a comma-separated EMAIL_TO value into clean addresses."""
    return [addr.strip() for addr in (raw or "").split(",") if addr.strip()]


# ── email bodies (pure — no network, no DB) ────────────────────────────────────


def build_subject(items: list[dict], today: date | None = None) -> str:
    day = (today or date.today()).isoformat()
    if not items:
        return f"GrantNova weekly grants — {day} — no new grants found"
    noun = "grant" if len(items) == 1 else "grants"
    return f"GrantNova weekly grants — {day} — {len(items)} {noun}"


def build_email_bodies(items: list[dict], today: date | None = None) -> tuple[str, str]:
    """
    Render the grant list as (html, plain_text).

    An empty list still produces a real message: silence should never be
    ambiguous between "no grants this week" and "the job broke".
    """
    day = (today or date.today()).isoformat()

    if not items:
        text = (
            f"GrantNova weekly grant search — {day}\n\n"
            "No new grants were found this week.\n\n"
            "This is a normal result, not an error — the search ran successfully.\n"
        )
        html = (
            f"<html><body style=\"font-family:Arial,Helvetica,sans-serif;color:#222\">"
            f"<h2>GrantNova weekly grant search</h2>"
            f"<p><strong>{escape(day)}</strong></p>"
            f"<p>No new grants were found this week.</p>"
            f"<p style=\"color:#666;font-size:13px\">This is a normal result, not an "
            f"error — the search ran successfully.</p>"
            f"</body></html>"
        )
        return html, text

    # ── plain text ──
    text_lines = [f"GrantNova weekly grant search — {day}", ""]
    text_lines.append(f"{len(items)} grant(s) found, best matches first:")
    text_lines.append("")
    for i, item in enumerate(items, start=1):
        text_lines.append(f"{i}. {item['title']}")
        text_lines.append(f"   Agency:   {item['funder']}")
        text_lines.append(f"   Deadline: {item['deadline']}")
        text_lines.append(f"   Apply:    {item['url']}")
        text_lines.append("")
    text_lines.append("Review and import these in GrantNova → Scout → Review Queue.")
    text = "\n".join(text_lines)

    # ── html ──
    rows = []
    for item in items:
        url = item["url"]
        if url and url != _NO_LINK:
            safe_url = escape(url, quote=True)
            link = f'<a href="{safe_url}">Apply / details</a>'
        else:
            link = '<span style="color:#888">No link available</span>'
        rows.append(
            "<tr>"
            f'<td style="padding:10px;border-bottom:1px solid #eee">'
            f'<strong>{escape(item["title"])}</strong></td>'
            f'<td style="padding:10px;border-bottom:1px solid #eee">'
            f'{escape(item["funder"])}</td>'
            f'<td style="padding:10px;border-bottom:1px solid #eee">'
            f'{escape(item["deadline"])}</td>'
            f'<td style="padding:10px;border-bottom:1px solid #eee">{link}</td>'
            "</tr>"
        )

    html = (
        '<html><body style="font-family:Arial,Helvetica,sans-serif;color:#222">'
        "<h2>GrantNova weekly grant search</h2>"
        f"<p><strong>{escape(day)}</strong> — {len(items)} grant(s) found, "
        "best matches first.</p>"
        '<table cellspacing="0" cellpadding="0" '
        'style="border-collapse:collapse;width:100%;font-size:14px">'
        '<thead><tr style="background:#f4f4f4;text-align:left">'
        '<th style="padding:10px">Grant</th>'
        '<th style="padding:10px">Agency</th>'
        '<th style="padding:10px">Deadline</th>'
        '<th style="padding:10px">Link</th>'
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
        '<p style="color:#666;font-size:13px;margin-top:18px">'
        "Review and import these in GrantNova → Scout → Review Queue. "
        "Deadlines marked <em>unverified</em> were auto-extracted — confirm them "
        "on the funder site before relying on them.</p>"
        "</body></html>"
    )
    return html, text


# ── sending ────────────────────────────────────────────────────────────────────


def send_email(
    sender: str,
    password: str,
    recipients: list[str],
    subject: str,
    html: str,
    text: str,
) -> None:
    """Send a multipart email over Gmail SMTP with STARTTLS."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=60) as smtp:
        smtp.starttls()
        smtp.login(sender, password)
        smtp.send_message(msg)


# ── scan ───────────────────────────────────────────────────────────────────────


def collect_grants(limit: int) -> list[dict]:
    """Run the discovery scan and return the top-ranked candidates as view dicts."""
    init_db()

    svc = DiscoveryService()
    db_gen = get_db()
    db = next(db_gen)
    try:
        for query in DEFAULT_QUERIES:
            log.info("Scanning: %s", query)
            try:
                staged = svc.run_search(db, query)
                log.info("  -> staged %d new candidate(s).", len(staged))
            except Exception as exc:  # noqa: BLE001 — one bad query must not kill the run
                log.warning("Query %r failed: %s", query, exc)

        return ScoutReportService().list_ranked_candidates(db, limit=limit)
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


# ── entry point ────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GrantNova weekly grant email")
    parser.add_argument(
        "--limit", type=int, default=DEFAULT_LIMIT,
        help=f"Max grants to include in the email (default {DEFAULT_LIMIT}).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run the scan and print the email instead of sending it.",
    )
    args = parser.parse_args(argv)

    # The email text uses em dashes and arrows. Windows consoles default to
    # cp1252 and would raise UnicodeEncodeError on --dry-run; the email body
    # itself is always UTF-8 regardless.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, OSError):  # pragma: no cover — non-standard stdout
        pass

    sender = os.environ.get("GMAIL_USER", "").strip()
    password = os.environ.get("GMAIL_APP_PASSWORD", "")
    recipients = parse_recipients(os.environ.get("EMAIL_TO", ""))

    # Validate config before spending several minutes on a scan we can't deliver.
    if not args.dry_run:
        missing = []
        if not sender:
            missing.append("GMAIL_USER")
        if not password:
            missing.append("GMAIL_APP_PASSWORD")
        if not recipients:
            missing.append("EMAIL_TO")
        if missing:
            print(
                f"ERROR: missing required environment variable(s): {', '.join(missing)}",
                file=sys.stderr,
            )
            return 1

    items = collect_grants(args.limit)
    subject = build_subject(items)
    html, text = build_email_bodies(items)

    if args.dry_run:
        print(f"Subject: {subject}")
        print(f"To: {', '.join(recipients) or '(EMAIL_TO not set)'}")
        print("-" * 60)
        print(text)
        return 0

    send_email(sender, password, recipients, subject, html, text)
    # Never log the password or the message body — only what was delivered.
    print(f"Sent {len(items)} grant(s) to {len(recipients)} recipient(s).")
    log.info("Weekly grant email sent to %d recipient(s).", len(recipients))
    return 0


if __name__ == "__main__":
    sys.exit(main())
