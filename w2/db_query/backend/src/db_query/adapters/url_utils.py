"""Normalize JDBC-style URLs for driver libraries (scheme typos, aliases)."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse

POSTGRES_URL_SCHEMES = frozenset({"postgresql", "postgres", "postgre"})
MYSQL_URL_SCHEMES = frozenset({"mysql", "mysql+pymysql", "mariadb"})


def rewrite_url_scheme(connection_url: str, new_scheme: str) -> str:
    parsed = urlparse(connection_url.strip())
    return urlunparse(parsed._replace(scheme=new_scheme))


def postgres_driver_url(connection_url: str) -> str:
    """Return a URL psycopg accepts; reject MySQL schemes with a clear error."""
    trimmed = connection_url.strip()
    scheme = urlparse(trimmed).scheme.lower()
    if scheme in MYSQL_URL_SCHEMES:
        raise ValueError(
            "MySQL URL passed to PostgreSQL driver. "
            "Use backendKind=mysql or restart the backend after upgrading."
        )
    if scheme not in POSTGRES_URL_SCHEMES:
        raise ValueError(
            f"Not a PostgreSQL URL (scheme={scheme!r}). "
            "Use postgres:// or postgresql://."
        )
    if scheme != "postgresql":
        return rewrite_url_scheme(trimmed, "postgresql")
    return trimmed
