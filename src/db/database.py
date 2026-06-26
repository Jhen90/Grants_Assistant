# ============================================================
# File: src/db/database.py
# Version: 1.1.0
# Created: 2026-06-25
# Modified: 2026-06-25
# Description: SQLAlchemy engine, session factory, Base, and init_db()
# ============================================================

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.utils.config import get_settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


def _build_engine() -> Engine:
    settings = get_settings()

    if settings.is_sqlite:
        # Ensure the data directory exists
        db_path = settings.db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)

        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )

        # Enable WAL mode and foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragmas(dbapi_conn, _connection_record):  # type: ignore[misc]
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    else:
        engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)

    return engine


engine = _build_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI / dependency-injection style session factory. Use as context manager in services."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables that don't yet exist. Called on app startup (not a replacement for Alembic)."""
    import src.models  # noqa: F401 — ensure all models are registered with Base.metadata

    Base.metadata.create_all(bind=engine)
    log.info("Database initialized (tables created if missing).")


def backup_db(backup_dir: str = "data/backups") -> Path:
    """
    SQLite-only: copy the live DB file to data/backups/ with a timestamp.
    Called automatically by Alembic env.py before each migration.
    """
    settings = get_settings()
    if not settings.is_sqlite:
        log.info("Backup skipped — not SQLite.")
        return Path()

    import shutil
    from datetime import datetime

    src_path = settings.db_path
    if not src_path.exists():
        log.info("No DB file to back up yet.")
        return Path()

    dest_dir = Path(backup_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = dest_dir / f"gmas_{timestamp}.db"
    shutil.copy2(src_path, dest)
    log.info("DB backed up to %s", dest)
    return dest
