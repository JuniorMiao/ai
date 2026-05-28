"""HTTP routes under `/api/v1/dbs*`."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, Response

from db_query.adapters import resolve_backend
from db_query.repositories import databases as db_repo
from db_query.schemas.databases import (
    DatabaseMetadataResponse,
    PutDatabaseBody,
    PutDatabaseResponse,
    RegisteredDatabaseListItem,
)

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
        adapter = resolve_backend(
            connection_url=body.url, backend_hint=body.backend_kind
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        meta = adapter.fetch_schema_metadata(body.url)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot connect or introspect database: {exc}",
        ) from exc

    meta.setdefault("backendKind", adapter.backend_id)
    payload = json.dumps(meta)
    db_repo.upsert_registration_and_metadata(
        conn,
        name=name,
        url=body.url,
        backend_kind=adapter.backend_id,
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
    """Re-run SQL introspection using the stored URL and update SQLite cache."""
    conn = request.app.state.db
    url = db_repo.get_connection_url(conn, name)
    if not url:
        raise HTTPException(status_code=404, detail="Unknown database name")
    hint = db_repo.get_backend_kind(conn, name)
    try:
        adapter = resolve_backend(connection_url=url, backend_hint=hint)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    now = _utc_now_iso()
    try:
        meta = adapter.fetch_schema_metadata(url)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot connect or introspect database: {exc}",
        ) from exc
    meta.setdefault("backendKind", adapter.backend_id)
    payload = json.dumps(meta)
    db_repo.replace_cached_metadata(
        conn,
        name=name,
        now_iso=now,
        metadata_json=payload,
        backend_kind=adapter.backend_id,
    )
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
