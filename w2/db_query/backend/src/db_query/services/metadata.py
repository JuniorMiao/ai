"""Schema introspection façade — delegates to pluggable :mod:`db_query.adapters`."""

from __future__ import annotations

from typing import Any

from db_query.adapters import resolve_backend


def fetch_schema_metadata(
    connection_url: str, *, backend_hint: str | None = None
) -> dict[str, Any]:
    """Return tables/columns suitable for UI cache and LLM context."""
    adapter = resolve_backend(connection_url=connection_url, backend_hint=backend_hint)
    snapshot = adapter.fetch_schema_metadata(connection_url)
    snapshot.setdefault("backendKind", adapter.backend_id)
    return snapshot
