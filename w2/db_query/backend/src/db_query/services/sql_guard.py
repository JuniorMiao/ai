"""Validate user SQL and enforce single SELECT + optional LIMIT injection."""

from __future__ import annotations

import sqlglot
from sqlglot import exp


class SqlGuardError(ValueError):
    """User SQL rejected before touching the target database."""


def prepare_select_sql(raw: str, max_rows: int) -> tuple[str, bool]:
    """Parse SQL; allow exactly one Postgres SELECT; inject LIMIT if missing."""
    stripped = raw.strip()
    if not stripped:
        raise SqlGuardError("SQL must not be empty")

    trees = sqlglot.parse(stripped, dialect="postgres")
    if len(trees) != 1:
        raise SqlGuardError("Exactly one SQL statement is allowed")

    tree = trees[0]
    if not isinstance(tree, exp.Select):
        raise SqlGuardError("Only SELECT queries are allowed")

    forbidden = tree.find(exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create)
    if forbidden:
        raise SqlGuardError("Only read-only SELECT is allowed")

    if tree.args.get("limit"):
        return tree.sql(dialect="postgres"), False

    limited = tree.limit(max_rows)
    return limited.sql(dialect="postgres"), True


def validate_and_apply_limit(raw: str, max_rows: int) -> tuple[str, bool]:
    """Alias used by Phase 4 tasks; identical to :func:`prepare_select_sql`."""
    return prepare_select_sql(raw, max_rows)
