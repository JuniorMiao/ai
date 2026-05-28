"""HTTP route for ``POST /api/v1/dbs/{name}/query`` (validated read-only SELECT)."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, Request

from db_query.adapters import resolve_backend
from db_query.config import get_settings
from db_query.repositories import databases as db_repo
from db_query.schemas.query import QueryRequest, QueryResult
from db_query.services.query_runner import run_select
from db_query.services.sql_guard import SqlGuardError, validate_and_apply_limit

router = APIRouter(prefix="/api/v1", tags=["query"])


def _require_registered_url(conn: sqlite3.Connection, name: str) -> str:
    url = db_repo.get_connection_url(conn, name)
    if not url:
        raise HTTPException(status_code=404, detail="Unknown database name")
    return url


@router.post("/dbs/{name}/query")
def execute_query(name: str, body: QueryRequest, request: Request) -> QueryResult:
    conn = request.app.state.db
    settings = get_settings()
    url = _require_registered_url(conn, name)
    hint = db_repo.get_backend_kind(conn, name)
    try:
        adapter = resolve_backend(connection_url=url, backend_hint=hint)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        sql_text, truncated = validate_and_apply_limit(
            body.sql,
            settings.query_max_rows,
            sqlglot_dialect=adapter.sqlglot_dialect,
        )
    except SqlGuardError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        columns, tuples = run_select(adapter, url, sql_text)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Query execution failed: {exc}",
        ) from exc
    rows_out = [list(t) for t in tuples]
    return QueryResult(
        columns=columns,
        rows=rows_out,
        truncated=truncated,
        max_rows=settings.query_max_rows,
    )
