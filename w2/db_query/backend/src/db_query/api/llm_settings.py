"""HTTP routes for `/api/v1/llm-settings`."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response

from db_query.repositories import llm_settings as llm_repo
from db_query.schemas.llm import (
    LlmProviderCatalogItem,
    LlmProviderCatalogResponse,
    LlmSettingsItem,
    LlmSettingsListResponse,
    PostLlmSettingsBody,
    PutLlmSettingsBody,
)
from db_query.services.llm_provider_registry import iter_provider_specs
from db_query.services.llm_providers import normalize_stored_provider

router = APIRouter(prefix="/api/v1", tags=["llm-settings"])


@router.get("/llm-providers", response_model=LlmProviderCatalogResponse)
def list_llm_providers() -> LlmProviderCatalogResponse:
    """Registered vendors (same source as ``LLM_PROVIDER_SPECS`` / :func:`iter_provider_specs`) for UI."""
    items: list[LlmProviderCatalogItem] = []
    for spec in iter_provider_specs():
        primary = spec.env_key_names[0] if spec.env_key_names else ""
        items.append(
            LlmProviderCatalogItem(
                id=spec.id,
                display_name=spec.display_name,
                short_name=spec.short_name,
                default_base_url=spec.default_base_url,
                default_model=spec.default_model,
                primary_api_key_env=primary,
                password_placeholder=spec.password_placeholder,
                api_key_inline_hint=spec.api_key_inline_hint,
            )
        )
    return LlmProviderCatalogResponse(items=items)


def _default_id_from_rows(rows: list) -> int | None:
    for r in rows:
        if r["is_default"]:
            return int(r["id"])
    return int(rows[0]["id"]) if rows else None


@router.get("/llm-settings")
def list_llm_settings(request: Request) -> LlmSettingsListResponse:
    conn = request.app.state.db
    rows = llm_repo.list_all(conn)
    items = [LlmSettingsItem(**llm_repo.row_to_item(r)) for r in rows]
    default_id = _default_id_from_rows(rows)
    return LlmSettingsListResponse(
        items=items,
        default_id=default_id,
        has_resolvable_key=llm_repo.any_resolvable_key(conn),
    )


@router.post("/llm-settings")
def create_llm_settings(body: PostLlmSettingsBody, request: Request) -> LlmSettingsItem:
    conn = request.app.state.db
    secret = body.api_key.strip() if body.api_key else None
    row = llm_repo.insert_profile(
        conn,
        provider=normalize_stored_provider(body.provider),
        base_url=body.base_url.strip(),
        model=body.model.strip(),
        api_key_ref=body.api_key_ref.strip() if body.api_key_ref else None,
        api_key_secret=secret,
        set_as_default=body.set_as_default,
    )
    return LlmSettingsItem(**llm_repo.row_to_item(row))


@router.put("/llm-settings/{profile_id}")
def update_llm_settings(
    profile_id: int, body: PutLlmSettingsBody, request: Request
) -> LlmSettingsItem:
    conn = request.app.state.db
    existing = llm_repo.get_by_id(conn, profile_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Unknown llm_settings id")

    unset = body.model_dump(exclude_unset=True)
    if "api_key" in unset:
        secret = body.api_key.strip() if body.api_key else None
    elif existing["api_key_secret"]:
        secret = str(existing["api_key_secret"])
    else:
        secret = None

    if "api_key_ref" in unset:
        api_ref = body.api_key_ref.strip() if body.api_key_ref else None
    elif existing["api_key_ref"]:
        api_ref = str(existing["api_key_ref"])
    else:
        api_ref = None

    row = llm_repo.update_profile(
        conn,
        profile_id,
        provider=normalize_stored_provider(body.provider),
        base_url=body.base_url.strip(),
        model=body.model.strip(),
        api_key_ref=api_ref,
        api_key_secret=secret,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Unknown llm_settings id")
    return LlmSettingsItem(**llm_repo.row_to_item(row))


@router.delete("/llm-settings/{profile_id}")
def delete_llm_settings(profile_id: int, request: Request) -> Response:
    conn = request.app.state.db
    if not llm_repo.delete_profile(conn, profile_id):
        raise HTTPException(status_code=404, detail="Unknown llm_settings id")
    return Response(status_code=204)


@router.post("/llm-settings/{profile_id}/default")
def set_default_llm(profile_id: int, request: Request) -> LlmSettingsItem:
    conn = request.app.state.db
    row = llm_repo.set_default(conn, profile_id)
    if not row:
        raise HTTPException(status_code=404, detail="Unknown llm_settings id")
    return LlmSettingsItem(**llm_repo.row_to_item(row))
