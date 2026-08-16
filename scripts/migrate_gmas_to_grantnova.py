# ============================================================
# File: scripts/migrate_gmas_to_grantnova.py
# Version: 1.2.0
# Created: 2026-07-16
# Modified: 2026-07-16
# Description: One-shot, idempotent data migration for the GMAS -> GrantNova rename.
#   Copies the real seed/operational data from the legacy `data/gmas.db` (which was
#   created by Base.metadata.create_all(), NOT Alembic — see TIP §3.1) into the new
#   Alembic-built `data/grantnova.db`.
#
#   Drift-safe: for each table it copies only the columns present in BOTH databases,
#   so a schema difference (e.g. columns added to a later migration) never aborts the
#   copy. Idempotent: uses INSERT OR IGNORE keyed on the existing primary key, so
#   re-running it does not duplicate rows.
#
#   Usage:
#     conda activate gmas
#     python -m scripts.migrate_gmas_to_grantnova            # copies default tables
#     python -m scripts.migrate_gmas_to_grantnova --verify   # only report row counts
# ============================================================

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

OLD_DB = Path("data/gmas.db")
NEW_DB = Path("data/grantnova.db")

# Tables that hold real data worth migrating (in FK-safe order).
TABLES = ["organizations", "funders", "selection_criteria", "templates"]


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def _count(conn: sqlite3.Connection, table: str) -> int:
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError:
        return -1  # table absent


def copy_table(old: sqlite3.Connection, new: sqlite3.Connection, table: str) -> int:
    old_cols = _columns(old, table)
    new_cols = _columns(new, table)
    shared = [c for c in old_cols if c in new_cols]
    if not shared:
        print(f"  {table}: no shared columns — skipped")
        return 0

    dropped = sorted(set(old_cols) - set(new_cols))
    added = sorted(set(new_cols) - set(old_cols))
    if dropped:
        print(f"  {table}: source-only columns not copied: {dropped}")
    if added:
        print(f"  {table}: target-only columns left at default: {added}")

    col_list = ", ".join(shared)
    placeholders = ", ".join("?" for _ in shared)
    rows = old.execute(f"SELECT {col_list} FROM {table}").fetchall()
    new.executemany(
        f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})", rows
    )
    new.commit()
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GMAS -> GrantNova data migration")
    parser.add_argument("--verify", action="store_true", help="Only report row counts.")
    args = parser.parse_args(argv)

    if not NEW_DB.exists():
        print(f"ERROR: {NEW_DB} does not exist. Run `alembic upgrade head` first.")
        return 1

    new = sqlite3.connect(NEW_DB)

    if args.verify or not OLD_DB.exists():
        if not OLD_DB.exists():
            print(f"(legacy {OLD_DB} absent — reporting target counts only)")
        for t in TABLES:
            print(f"  {t}: grantnova={_count(new, t)}")
        new.close()
        return 0

    old = sqlite3.connect(OLD_DB)
    print(f"Migrating data: {OLD_DB} -> {NEW_DB}")
    for t in TABLES:
        before = _count(new, t)
        copied = copy_table(old, new, t)
        after = _count(new, t)
        print(f"  {t}: source={_count(old, t)} copied={copied} target {before}->{after}")

    old.close()
    new.close()
    print("Data migration complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
