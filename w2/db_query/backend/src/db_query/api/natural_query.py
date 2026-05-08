"""HTTP route for natural-language SQL generation under `/api/v1/dbs/*/query/natural`.

Product choice (T036): **Return validated SQL only** — does not execute against PostgreSQL.
Users confirm or edit in the UI, then POST `/api/v1/dbs/{name}/query` as usual.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from db_query.config import get_settings
from db_query.repositories import databases as db_repo
from db_query.repositories import llm_settings as llm_repo
from db_query.schemas.databases import NaturalQueryRequest, NaturalQueryResponse
from db_query.services.llm_errors import map_llm_upstream_error
from db_query.services.llm_providers import resolve_endpoint_for_row
from db_query.services.nl_sql import generate_sql_from_prompt
from db_query.services.sql_guard import SqlGuardError, validate_and_apply_limit

router = APIRouter(prefix="/api/v1", tags=["natural-query"])


@router.post("/dbs/{name}/query/natural")
def natural_query(name: str, body: NaturalQueryRequest, request: Request) -> NaturalQueryResponse:
    conn = request.app.state.db
    settings = get_settings()

    if not db_repo.get_connection_url(conn, name):
        raise HTTPException(status_code=404, detail="Unknown database name")

    cached = db_repo.get_cached_metadata(conn, name)
    if not cached:
        raise HTTPException(
            status_code=503,
            detail="No cached metadata for this database; refresh the connection first.",
        )
    payload, _fetched_at = cached

    if body.llm_settings_id is not None:
        llm_row = llm_repo.get_by_id(conn, body.llm_settings_id)
        if not llm_row:
            raise HTTPException(status_code=404, detail="Unknown llm_settings id")
    else:
        llm_row = llm_repo.get_default_row(conn)
    api_key = llm_repo.resolve_api_key(llm_row)
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="LLM is not configured: save API settings under /api/v1/llm-settings "
            "or set OPENAI_API_KEY / DASHSCOPE_API_KEY (通义千问).",
        )

    base_url, model = resolve_endpoint_for_row(llm_row)

    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt must not be empty")

    try:
        sql_raw, warnings = generate_sql_from_prompt(
            payload,
            prompt,
            base_url=base_url,
            api_key=api_key,
            model=model,
        )
    except Exception as exc:
        status, detail = map_llm_upstream_error(exc)
        raise HTTPException(status_code=status, detail=detail) from exc

    try:
        sql_text, _truncated = validate_and_apply_limit(sql_raw, settings.query_max_rows)
    except SqlGuardError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Generated SQL failed validation: {exc}",
        ) from exc

    guard_note = "SQL was validated and normalized (including default LIMIT if missing)."
    out_warnings = [*warnings, guard_note]
    return NaturalQueryResponse(sql=sql_text, warnings=out_warnings)
