"""Central registry of SQL backends — add new drivers here only (open for extension)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from db_query.adapters.base import SqlBackendAdapter

_FACTORY: dict[str, type[SqlBackendAdapter]] = {}


def register_backend(
    backend_id: str,
) -> Callable[[type[SqlBackendAdapter]], type[SqlBackendAdapter]]:
    """Class decorator: ``@register_backend("mysql") class MysqlBackend: ...``."""

    def _wrap(cls: type[SqlBackendAdapter]) -> type[SqlBackendAdapter]:
        key = backend_id.strip().lower()
        _FACTORY[key] = cls
        return cls

    return _wrap


def get_adapter(backend_id: str) -> SqlBackendAdapter:
    """Return a stateless adapter instance for the given logical backend id."""
    key = backend_id.strip().lower()
    cls = _FACTORY.get(key)
    if cls is None:
        supported = ", ".join(sorted(_FACTORY)) if _FACTORY else "(none)"
        raise ValueError(f"Unknown backend {backend_id!r}. Supported: {supported}")
    return cls()


def known_backend_ids() -> frozenset[str]:
    return frozenset(_FACTORY)
