# ============================================================
# File: scripts/run_discovery_scan.py
# Version: 1.2.0
# Created: 2026-06-30
# Modified: 2026-06-30
# Description: Scheduled discovery scan. Runs a saved set of queries through the
#   discovery pipeline and stages new candidates for human review. Designed to
#   be run by Windows Task Scheduler (e.g. weekly).
#
#   Usage:
#     conda activate gmas
#     python -m scripts.run_discovery_scan
#     python -m scripts.run_discovery_scan --queries "youth STEM grant MA" "climate education grant"
#
#   Task Scheduler (weekly, Mondays 7am) — create with:
#     schtasks /Create /SC WEEKLY /D MON /ST 07:00 /TN "GMAS Discovery Scan" ^
#       /TR "cmd /c cd /d C:\path\to\Grants_Assistant && conda activate gmas && python -m scripts.run_discovery_scan"
# ============================================================

from __future__ import annotations

import argparse
import sys

from src.db.database import get_db, init_db
from src.services.discovery_service import DiscoveryService
from src.utils.logger import get_logger

log = get_logger("discovery_scan")

# Default saved searches — tuned to The Dojo's profile. Edit to taste.
DEFAULT_QUERIES = [
    "youth development grant Massachusetts 2026",
    "STEM education grant nonprofit Boston teens 2026",
    "climate education youth grant Massachusetts",
    "workforce development youth grant Boston",
    "girls in STEM grant 2026",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GMAS scheduled discovery scan")
    parser.add_argument(
        "--queries", nargs="*", default=None,
        help="Override the default saved searches.",
    )
    parser.add_argument(
        "--sources", nargs="*", default=None,
        help="Limit to specific source connectors (e.g. grants.gov web_search).",
    )
    parser.add_argument(
        "--limit", type=int, default=15, help="Max results per source per query.",
    )
    parser.add_argument(
        "--sweep", action="store_true",
        help="Run the full 'search everywhere' sweep (org-profile query expansion "
             "+ all known funder sites + public portals) instead of fixed queries.",
    )
    args = parser.parse_args(argv)

    init_db()

    svc = DiscoveryService()
    db_gen = get_db()
    db = next(db_gen)

    total = 0
    try:
        if args.sweep:
            log.info("Running full 'search everywhere' sweep.")
            staged = svc.run_full_sweep(db, sources=args.sources, limit_per_source=args.limit)
            total = len(staged)
        else:
            queries = args.queries or DEFAULT_QUERIES
            for query in queries:
                log.info("Scanning: %s", query)
                staged = svc.run_search(
                    db, query, sources=args.sources, limit_per_source=args.limit
                )
                total += len(staged)
                log.info("  → staged %d new candidate(s).", len(staged))
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass

    log.info("Discovery scan complete. %d new candidate(s) staged across %d queries.",
             total, len(queries))
    print(f"Discovery scan complete: {total} new candidate(s) staged. "
          f"Review them in the Discover → Review Queue tab.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
