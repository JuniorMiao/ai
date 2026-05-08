"""SQLite persistence for registered PostgreSQL connections and cached metadata."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from db_query.schemas.databases import RegisteredDatabaseListItem


def list_registered(conn: sqlite3.Connection) -> list[RegisteredDatabaseListItem]:
    cur = conn.execute(
        "SELECT name, created_at, updated_at FROM registered_database ORDER BY name"
    )
    return [
        RegisteredDatabaseListItem(
            name=r["name"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
        for r in cur.fetchall()
    ]


def get_connection_url(conn: sqlite3.Connection, name: str) -> str | None:
    row = conn.execute(
        "SELECT url FROM registered_database WHERE name = ?", (name,)
    ).fetchone()
    return str(row[0]) if row else None


def upsert_registration_and_metadata(
    conn: sqlite3.Connection,
    *,
    name: str,
    url: str,
    now_iso: str,
    metadata_json: str,
) -> None:
    conn.execute(
        """
        INSERT INTO registered_database (name, url, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
          url = excluded.url,
          updated_at = excluded.updated_at
        """,
        (name, url, now_iso, now_iso),
    )
    conn.execute(
        """
        INSERT INTO database_metadata (db_name, payload_json, fetched_at, schema_version)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(db_name) DO UPDATE SET
          payload_json = excluded.payload_json,
          fetched_at = excluded.fetched_at,
          schema_version = excluded.schema_version
        """,
        (name, metadata_json, now_iso),
    )
    conn.commit()


def get_cached_metadata(
    conn: sqlite3.Connection, name: str
) -> tuple[dict[str, Any], str] | None:
    row = conn.execute(
        """
        SELECT m.payload_json, m.fetched_at
        FROM database_metadata m
        WHERE m.db_name = ?
        """,
        (name,),
    ).fetchone()
    if not row:
        return None
    return json.loads(row[0]), str(row[1])


def get_created_at(conn: sqlite3.Connection, name: str) -> str | None:
    row = conn.execute(
        "SELECT created_at FROM registered_database WHERE name = ?", (name,)
    ).fetchone()
    return str(row[0]) if row else None


def delete_registered(conn: sqlite3.Connection, name: str) -> bool:
    """Remove registration and cached metadata (explicit deletes for all SQLite modes)."""
    conn.execute("DELETE FROM database_metadata WHERE db_name = ?", (name,))
    cur = conn.execute("DELETE FROM registered_database WHERE name = ?", (name,))
    conn.commit()
    return cur.rowcount > 0


def replace_cached_metadata(
    conn: sqlite3.Connection,
    *,
    name: str,
    now_iso: str,
    metadata_json: str,
) -> None:
    """Refresh introspection snapshot and bump ``registered_database.updated_at``."""
    conn.execute(
        "UPDATE registered_database SET updated_at = ? WHERE name = ?",
        (now_iso, name),
    )
    conn.execute(
        """
        INSERT INTO database_metadata (db_name, payload_json, fetched_at, schema_version)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(db_name) DO UPDATE SET
          payload_json = excluded.payload_json,
          fetched_at = excluded.fetched_at,
          schema_version = excluded.schema_version
        """,
        (name, metadata_json, now_iso),
    )
    conn.commit()
