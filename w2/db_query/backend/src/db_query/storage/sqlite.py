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
    _migrate_llm_settings(conn)
    _migrate_registered_database_backend(conn)


def _migrate_llm_settings(conn: sqlite3.Connection) -> None:
    """Add columns introduced after first schema version."""
    info = conn.execute("PRAGMA table_info(llm_settings)").fetchall()
    cols = {str(r[1]) for r in info}
    if "api_key_secret" not in cols:
        conn.execute("ALTER TABLE llm_settings ADD COLUMN api_key_secret TEXT")
        conn.commit()


def _migrate_registered_database_backend(conn: sqlite3.Connection) -> None:
    """Persist logical SQL backend kind (PostgreSQL / MySQL / …) per registration."""
    info = conn.execute("PRAGMA table_info(registered_database)").fetchall()
    cols = {str(r[1]) for r in info}
    if "backend_kind" not in cols:
        conn.execute("ALTER TABLE registered_database ADD COLUMN backend_kind TEXT")
        conn.commit()

    from db_query.adapters.resolver import infer_backend_id

    rows = conn.execute(
        """
        SELECT name, url FROM registered_database
        WHERE backend_kind IS NULL OR TRIM(backend_kind) = ''
        """
    ).fetchall()
    if not rows:
        return

    updates: list[tuple[str, str]] = []
    for r in rows:
        name = str(r["name"])
        raw_url = str(r["url"])
        try:
            bid = infer_backend_id(raw_url)
        except ValueError:
            continue
        updates.append((bid, name))
    if not updates:
        return
    conn.executemany("UPDATE registered_database SET backend_kind = ? WHERE name = ?", updates)
    conn.commit()


def load_schema_sql() -> str:
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    return schema_path.read_text(encoding="utf-8")


def open_app_database(settings: Settings) -> sqlite3.Connection:
    """Connect using ``settings.sqlite_path`` and run schema bootstrap on startup."""
    conn = connect(settings.sqlite_path)
    init_schema(conn, load_schema_sql())
    return conn
