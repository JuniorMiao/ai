"""SQLite connection and schema bootstrap.

Connection path comes from :func:`db_query.config.get_settings` (environment variable
``DB_QUERY_SQLITE_PATH``); when unset, defaults next to ``w2/db_query/db_query.db``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db_query.config import Settings


def connect(path: Path) -> sqlite3.Connection:
    """Open a SQLite database file (creating parent directories when needed)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection, schema_sql: str) -> None:
    """Apply DDL / migrations script idempotently."""
    conn.executescript(schema_sql)
    conn.commit()


def load_schema_sql() -> str:
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    return schema_path.read_text(encoding="utf-8")


def open_app_database(settings: Settings) -> sqlite3.Connection:
    """Connect using ``settings.sqlite_path`` and run schema bootstrap on startup."""
    conn = connect(settings.sqlite_path)
    init_schema(conn, load_schema_sql())
    return conn
