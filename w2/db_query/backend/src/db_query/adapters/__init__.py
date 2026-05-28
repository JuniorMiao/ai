"""Pluggable SQL backends (PostgreSQL, MySQL, …). Importing this module registers defaults."""

from __future__ import annotations

# Register built-in adapters (side effect on import).
from db_query.adapters import mysql as _mysql  # noqa: F401
from db_query.adapters import postgres as _postgres  # noqa: F401
from db_query.adapters.base import SqlBackendAdapter
from db_query.adapters.registry import get_adapter, known_backend_ids, register_backend
from db_query.adapters.resolver import infer_backend_id, resolve_backend

__all__ = [
    "SqlBackendAdapter",
    "get_adapter",
    "infer_backend_id",
    "known_backend_ids",
    "register_backend",
    "resolve_backend",
]
