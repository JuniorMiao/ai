"""Run validated read-only SQL against the registered connection URL."""

from __future__ import annotations

from typing import Any

from db_query.adapters.base import SqlBackendAdapter


def run_select(
    adapter: SqlBackendAdapter, connection_url: str, sql: str
) -> tuple[list[str], list[tuple[Any, ...]]]:
    return adapter.execute_select(connection_url, sql)
