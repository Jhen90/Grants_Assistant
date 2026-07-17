# ============================================================
# File: tests/integration/test_migrations.py
# Version: 1.2.0
# Created: 2026-07-16
# Modified: 2026-07-16
# Description: Guards for the Alembic migration chain (GrantNova).
#   - Reversibility: upgrade head -> downgrade base -> upgrade head must succeed
#     on a throwaway DB (NFR-SCOUT-007).
#   - Drift guard: the schema Alembic produces must match the ORM models built by
#     Base.metadata.create_all (NFR-SCOUT-006) — this is exactly the divergence that
#     had left the live DB without a `discovered_candidates` table.
#   No test here touches the real data/grantnova.db.
# ============================================================

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import sqlite3

from sqlalchemy import create_engine, inspect

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_alembic(db_url: str, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, DATABASE_URL=db_url, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def _tables(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    finally:
        conn.close()
    return {r[0] for r in rows} - {"alembic_version", "sqlite_sequence"}


def test_migration_roundtrip(tmp_path):
    """upgrade head -> downgrade base -> upgrade head, all clean, table present at end."""
    db = tmp_path / "roundtrip.db"
    url = f"sqlite:///{db.as_posix()}"

    up1 = _run_alembic(url, "upgrade", "head")
    assert up1.returncode == 0, up1.stderr
    assert "discovered_candidates" in _tables(db)

    down = _run_alembic(url, "downgrade", "base")
    assert down.returncode == 0, down.stderr
    assert _tables(db) == set()  # all app tables removed

    up2 = _run_alembic(url, "upgrade", "head")
    assert up2.returncode == 0, up2.stderr
    assert "discovered_candidates" in _tables(db)


def test_no_orm_migration_drift(tmp_path):
    """Alembic-built schema must equal the ORM create_all schema, table + columns."""
    # Schema A: built from the Alembic chain.
    alembic_db = tmp_path / "alembic.db"
    res = _run_alembic(f"sqlite:///{alembic_db.as_posix()}", "upgrade", "head")
    assert res.returncode == 0, res.stderr

    # Schema B: built from the ORM models directly.
    import src.models  # noqa: F401 — registers all models
    from src.db.database import Base

    orm_db = tmp_path / "orm.db"
    eng = create_engine(f"sqlite:///{orm_db.as_posix()}")
    Base.metadata.create_all(eng)

    a_tables = _tables(alembic_db)
    b_tables = _tables(orm_db)
    assert a_tables == b_tables, (
        f"table drift — alembic-only: {a_tables - b_tables}, "
        f"orm-only: {b_tables - a_tables}"
    )

    # Column-level parity per shared table.
    insp_a = inspect(create_engine(f"sqlite:///{alembic_db.as_posix()}"))
    insp_b = inspect(eng)
    drift = {}
    for t in sorted(a_tables):
        cols_a = {c["name"] for c in insp_a.get_columns(t)}
        cols_b = {c["name"] for c in insp_b.get_columns(t)}
        if cols_a != cols_b:
            drift[t] = {"alembic_only": cols_a - cols_b, "orm_only": cols_b - cols_a}
    assert not drift, f"column drift between Alembic and ORM: {drift}"
