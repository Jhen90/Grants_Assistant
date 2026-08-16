# ============================================================
# File: src/db/migrations/env.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: Alembic env.py — imports all models, backs up SQLite before migration
# ============================================================

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add project root to sys.path so src.* imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.db.database import Base, backup_db  # noqa: E402
import src.models  # noqa: F401, E402 — registers all models with Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use DATABASE_URL env var if set; otherwise fall back to alembic.ini value
db_url = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Back up SQLite before applying migrations
    if db_url and db_url.startswith("sqlite"):
        backup_db()

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
