"""Resolve effective LLM endpoint defaults — facade over :mod:`llm_provider_registry`.

Prefer importing :mod:`llm_provider_registry` for new code; this module keeps a stable
API used by routes and tests.
"""

from __future__ import annotations

import sqlite3

from db_query.services.llm_provider_registry import (
    LLM_PROVIDER_SPECS,
    canonical_provider_id,
    get_spec_by_id,
)

# Backward-compat constants (derived from registry)
_OPENAI = get_spec_by_id("openai")
_QWEN = get_spec_by_id("qwen")

DASHSCOPE_COMPAT_BASE = _QWEN.default_base_url
OPENAI_DEFAULT_BASE = _OPENAI.default_base_url
OPENAI_DEFAULT_MODEL = _OPENAI.default_model
QWEN_DEFAULT_MODEL = _QWEN.default_model


def normalize_stored_provider(provider: str) -> str:
    """Persist-friendly canonical id (see :func:`canonical_provider_id`)."""
    return canonical_provider_id(provider)


def is_qwen_family(provider: str) -> bool:
    """True when the resolved vendor is Qwen/DashScope."""
    return canonical_provider_id(provider) == "qwen"


def defaults_for_provider(provider: str) -> tuple[str, str]:
    """Return ``(base_url, model)`` defaults for a stored ``provider`` string."""
    spec = get_spec_by_id(canonical_provider_id(provider))
    return spec.default_base_url, spec.default_model


def resolve_endpoint_for_row(row: sqlite3.Row | None) -> tuple[str, str]:
    """
    Effective ``base_url`` and ``model`` for chat completions.

    Empty stored values are filled from the resolved provider spec.
    """
    if row is None:
        s = get_spec_by_id("openai")
        return s.default_base_url, s.default_model
    spec = get_spec_by_id(canonical_provider_id(str(row["provider"] or "")))
    base = str(row["base_url"] or "").strip() or spec.default_base_url
    model = str(row["model"] or "").strip() or spec.default_model
    return base, model


def provider_spec_ids() -> tuple[str, ...]:
    """Canonical ids for APIs/UI validation (extension hook)."""
    return tuple(s.id for s in LLM_PROVIDER_SPECS)
