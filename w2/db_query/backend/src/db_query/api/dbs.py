"""HTTP routes under `/api/v1/dbs*`."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, Response

from db_query.config import get_settings
from db_query.repositories import databases as db_repo
from db_query.schemas.databases import (
    DatabaseMetadataResponse,
    NaturalQueryRequest,
    NaturalQueryResponse,
    PutDatabaseBody,
    PutDatabaseResponse,
    QueryRequest,
    QueryResult,
    RegisteredDatabaseListItem,
)
from db_query.services.metadata import fetch_schema_metadata
from db_query.services.nl_sql import generate_sql_from_prompt
from db_query.services.query_pg import run_select
from db_query.services.sql_guard import SqlGuardError, prepare_select_sql

router = APIRouter(prefix="/api/v1", tags=["dbs"])


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _require_registered_url(conn: sqlite3.Connection, name: str) -> str:
    url = db_repo.get_connection_url(conn, name)
    if not url:
        raise HTTPException(status_code=404, detail="Unknown database name")
    return url


@router.get("/dbs")
def list_databases(request: Request) -> list[RegisteredDatabaseListItem]:
    conn = request.app.state.db
    return db_repo.list_registered(conn)


@router.put("/dbs/{name}")
def register_database(name: str, body: PutDatabaseBody, request: Request) -> PutDatabaseResponse:
    conn = request.app.state.db
    now = _utc_now_iso()
    try:
        meta = fetch_schema_metadata(body.url)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot connect or introspect database: {exc}",
        ) from exc

    payload = json.dumps(meta)
    db_repo.upsert_registration_and_metadata(
        conn,
        name=name,
        url=body.url,
        now_iso=now,
        metadata_json=payload,
    )

    created_at = db_repo.get_created_at(conn, name) or now
    return PutDatabaseResponse(name=name, created_at=created_at)


@router.delete("/dbs/{name}")
def delete_database(name: str, request: Request) -> Response:
    conn = request.app.state.db
    if not db_repo.delete_registered(conn, name):
        raise HTTPException(status_code=404, detail="Unknown database name")
    return Response(status_code=204)


@router.post("/dbs/{name}/refresh")
def refresh_database_metadata(name: str, request: Request) -> DatabaseMetadataResponse:
    """Re-run PostgreSQL introspection using the stored URL and update SQLite cache."""
    conn = request.app.state.db
    url = db_repo.get_connection_url(conn, name)
    if not url:
        raise HTTPException(status_code=404, detail="Unknown database name")
    now = _utc_now_iso()
    try:
        meta = fetch_schema_metadata(url)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot connect or introspect database: {exc}",
        ) from exc
    payload = json.dumps(meta)
    db_repo.replace_cached_metadata(conn, name=name, now_iso=now, metadata_json=payload)
    return DatabaseMetadataResponse(
        name=name,
        schema_snapshot=meta,
        fetched_at=now,
    )


@router.get("/dbs/{name}")
def get_database_metadata(name: str, request: Request) -> DatabaseMetadataResponse:
    conn = request.app.state.db
    row = db_repo.get_cached_metadata(conn, name)
    if not row:
        raise HTTPException(status_code=404, detail="Unknown database name")
    payload, fetched_at = row
    return DatabaseMetadataResponse(
        name=name,
        schema_snapshot=payload,
        fetched_at=fetched_at,
    )


@router.post("/dbs/{name}/query")
def execute_query(name: str, body: QueryRequest, request: Request) -> QueryResult:
    conn = request.app.state.db
    settings = get_settings()
    url = _require_registered_url(conn, name)
    try:
        sql_text, truncated = prepare_select_sql(body.sql, settings.query_max_rows)
    except SqlGuardError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        columns, tuples = run_select(url, sql_text)
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


@router.post("/dbs/{name}/query/natural")
def natural_query(name: str, body: NaturalQueryRequest, request: Request) -> NaturalQueryResponse:
    conn = request.app.state.db
    url = _require_registered_url(conn, name)
    try:
        sql_text, warnings = generate_sql_from_prompt(url, body.prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Natural language generation failed: {exc}",
        ) from exc
    return NaturalQueryResponse(sql=sql_text, warnings=warnings)
