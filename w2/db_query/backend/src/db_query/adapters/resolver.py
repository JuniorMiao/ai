"""Map connection URLs (+ optional hints) to a registered SqlBackendAdapter."""


from __future__ import annotations

from urllib.parse import urlparse

from db_query.adapters.base import SqlBackendAdapter
from db_query.adapters.registry import get_adapter, known_backend_ids

# First matching registered backend wins for ambiguous schemes later; extend maps only.
_SCHEME_TO_BACKEND: dict[str, str] = {
    "postgres": "postgres",
    "postgresql": "postgres",
    "postgre": "postgres",
    "mysql": "mysql",
    "mysql+pymysql": "mysql",
    "mariadb": "mysql",
}


def infer_backend_id(connection_url: str) -> str:
    """Infer logical backend id from URL scheme."""
    trimmed = connection_url.strip()
    if not trimmed:
        raise ValueError("Connection URL must not be empty")
    parsed = urlparse(trimmed)
    scheme = parsed.scheme.lower()
    if scheme not in _SCHEME_TO_BACKEND:
        supported = ", ".join(sorted(set(_SCHEME_TO_BACKEND)))
        raise ValueError(
            f"Unsupported URL scheme {scheme!r}. "
            f"Use one of: {supported}. "
            f"Alternatively pass backendKind explicitly when registering."
        )
    return _SCHEME_TO_BACKEND[scheme]


def _try_infer_backend_id(connection_url: str) -> str | None:
    try:
        return infer_backend_id(connection_url)
    except ValueError:
        return None


def resolve_backend(
    *,
    connection_url: str,
    backend_hint: str | None = None,
) -> SqlBackendAdapter:
    """
    Choose adapter for a registered connection.

    When the URL scheme is recognized (``mysql://``, ``postgres://``, …), it **always**
    wins over ``backend_hint`` so a mismatched dropdown value cannot route MySQL URLs
    to PostgreSQL drivers (and vice versa).

    ``backend_hint`` is used only when the URL scheme cannot be inferred.
    """
    trimmed = connection_url.strip()
    if not trimmed:
        raise ValueError("Connection URL must not be empty")

    inferred = _try_infer_backend_id(trimmed)
    if inferred is not None:
        return get_adapter(inferred)

    if backend_hint is not None and backend_hint.strip():
        bid = backend_hint.strip().lower()
        if bid not in known_backend_ids():
            supported = ", ".join(sorted(known_backend_ids()))
            raise ValueError(f"Unknown backendKind {backend_hint!r}. Supported: {supported}")
        return get_adapter(bid)

    supported = ", ".join(sorted(set(_SCHEME_TO_BACKEND)))
    raise ValueError(
        f"Cannot infer backend from connection URL. "
        f"Use a recognized scheme ({supported}) or pass backendKind."
    )
