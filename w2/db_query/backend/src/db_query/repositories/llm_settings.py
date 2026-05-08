"""SQLite persistence for ``llm_settings`` (multiple profiles + one default)."""

from __future__ import annotations

import os
import sqlite3
from typing import Any

from db_query.services.llm_provider_registry import (
    all_registered_env_var_names,
    canonical_provider_id,
    env_probe_order_rowless,
    get_spec_by_id,
)


def _count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) FROM llm_settings").fetchone()
    return int(row[0]) if row else 0


def list_all(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    cur = conn.execute(
        "SELECT * FROM llm_settings ORDER BY is_default DESC, id ASC"
    )
    return list(cur.fetchall())


def get_by_id(conn: sqlite3.Connection, profile_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM llm_settings WHERE id = ?", (profile_id,)
    ).fetchone()


def get_default_row(conn: sqlite3.Connection) -> sqlite3.Row | None:
    row = conn.execute(
        "SELECT * FROM llm_settings WHERE is_default = 1 ORDER BY id LIMIT 1"
    ).fetchone()
    if row:
        return row
    return conn.execute("SELECT * FROM llm_settings ORDER BY id LIMIT 1").fetchone()


def row_to_item(row: sqlite3.Row) -> dict[str, Any]:
    has_secret = bool(row["api_key_secret"])
    ref = row["api_key_ref"]
    has_ref = bool(ref and str(ref).strip())
    return {
        "id": int(row["id"]),
        "provider": str(row["provider"]),
        "base_url": str(row["base_url"]),
        "model": str(row["model"]),
        "api_key_ref": str(ref) if ref else None,
        "has_api_key": has_secret or has_ref,
        "is_default": bool(row["is_default"]),
    }


def resolve_api_key(row: sqlite3.Row | None) -> str | None:
    """Resolve API key: inline secret, env ref, then provider-aware env fallbacks."""
    if row is None:
        for name in env_probe_order_rowless():
            v = os.getenv(name)
            if v:
                return v
        return None

    secret = row["api_key_secret"]
    if secret:
        return str(secret)
    ref = row["api_key_ref"]
    if ref:
        name = str(ref).strip()
        if name:
            v = os.getenv(name)
            if v:
                return v

    spec = get_spec_by_id(canonical_provider_id(str(row["provider"] or "")))
    for name in spec.env_key_names:
        v = os.getenv(name)
        if v:
            return v
    return None


def any_resolvable_key(conn: sqlite3.Connection) -> bool:
    if any(os.getenv(n) for n in all_registered_env_var_names()):
        return True
    for row in list_all(conn):
        if resolve_api_key(row):
            return True
    return False


def _clear_default_flags(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE llm_settings SET is_default = 0")


def insert_profile(
    conn: sqlite3.Connection,
    *,
    provider: str,
    base_url: str,
    model: str,
    api_key_ref: str | None,
    api_key_secret: str | None,
    set_as_default: bool,
) -> sqlite3.Row:
    n = _count(conn)
    make_default = set_as_default or n == 0
    if make_default:
        _clear_default_flags(conn)
    conn.execute(
        """
        INSERT INTO llm_settings (
            provider, base_url, api_key_ref, api_key_secret, model, is_default
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (provider, base_url, api_key_ref, api_key_secret, model, 1 if make_default else 0),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM llm_settings WHERE id = last_insert_rowid()"
    ).fetchone()
    assert row is not None
    return row


def update_profile(
    conn: sqlite3.Connection,
    profile_id: int,
    *,
    provider: str,
    base_url: str,
    model: str,
    api_key_ref: str | None,
    api_key_secret: str | None,
) -> sqlite3.Row | None:
    cur = conn.execute(
        """
        UPDATE llm_settings SET
          provider = ?,
          base_url = ?,
          api_key_ref = ?,
          api_key_secret = ?,
          model = ?
        WHERE id = ?
        """,
        (provider, base_url, api_key_ref, api_key_secret, model, profile_id),
    )
    conn.commit()
    if cur.rowcount == 0:
        return None
    return get_by_id(conn, profile_id)


def delete_profile(conn: sqlite3.Connection, profile_id: int) -> bool:
    row = get_by_id(conn, profile_id)
    if not row:
        return False
    was_default = bool(row["is_default"])
    conn.execute("DELETE FROM llm_settings WHERE id = ?", (profile_id,))
    conn.commit()
    if was_default and _count(conn) > 0:
        first = conn.execute(
            "SELECT id FROM llm_settings ORDER BY id LIMIT 1"
        ).fetchone()
        if first:
            set_default(conn, int(first[0]))
    return True


def set_default(conn: sqlite3.Connection, profile_id: int) -> sqlite3.Row | None:
    if not get_by_id(conn, profile_id):
        return None
    _clear_default_flags(conn)
    conn.execute(
        "UPDATE llm_settings SET is_default = 1 WHERE id = ?", (profile_id,)
    )
    conn.commit()
    return get_by_id(conn, profile_id)
