"""Run validated read-only SQL against the registered PostgreSQL URL."""

from __future__ import annotations

from db_query.services.query_pg import run_select

__all__ = ["run_select"]
