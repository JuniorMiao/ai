"""Registered LLM vendors — single place to extend providers (OCP).

Adding a vendor: append a new :class:`LlmProviderSpec` to ``LLM_PROVIDER_SPECS``.
Call sites use :func:`canonical_provider_id`, :func:`get_spec_by_id`, and
:func:`env_probe_order_rowless` only; they do not branch on vendor names.

All current integrations use the OpenAI-compatible chat-completions shape;
protocol-specific clients would live beside new specs and be selected by ``id``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# DashScope OpenAI-compatible API (通义千问)
# https://help.aliyun.com/zh/model-studio/developer-reference/use-qwen-by-calling-api
_DASHSCOPE_COMPAT_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass(frozen=True, slots=True)
class LlmProviderSpec:
    """Immutable description of one persisted ``provider`` value (`llm_settings.provider`)."""

    id: str
    display_name: str
    short_name: str
    default_base_url: str
    default_model: str
    #: Env vars to try when no inline key / ``api_key_ref`` resolves (order matters).
    env_key_names: tuple[str, ...]
    #: Legacy UI/API tokens that normalize to :attr:`id`.
    aliases: frozenset[str] = frozenset()
    password_placeholder: str = ""
    api_key_inline_hint: str = ""


LLM_PROVIDER_SPECS: Final[tuple[LlmProviderSpec, ...]] = (
    LlmProviderSpec(
        id="openai",
        display_name="OpenAI",
        short_name="OpenAI",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        env_key_names=("OPENAI_API_KEY", "DASHSCOPE_API_KEY"),
        password_placeholder="sk-...",
        api_key_inline_hint="OpenAI API Key，写入本地数据库",
    ),
    LlmProviderSpec(
        id="qwen",
        display_name="阿里云通义千问（DashScope 兼容模式）",
        short_name="通义千问",
        default_base_url=_DASHSCOPE_COMPAT_BASE,
        default_model="qwen-turbo",
        env_key_names=("DASHSCOPE_API_KEY", "OPENAI_API_KEY"),
        aliases=frozenset({"dashscope", "alibaba", "tyqw", "tongyi", "通义"}),
        password_placeholder="DashScope Key",
        api_key_inline_hint="阿里云 DashScope API Key（与控制台一致），写入本地数据库",
    ),
)

_BY_ID: dict[str, LlmProviderSpec] = {s.id: s for s in LLM_PROVIDER_SPECS}
_DEFAULT_SPEC: LlmProviderSpec = _BY_ID["openai"]


def iter_provider_specs() -> tuple[LlmProviderSpec, ...]:
    """All registered providers (stable order: registration order)."""
    return LLM_PROVIDER_SPECS


def get_spec_by_id(canonical_id: str) -> LlmProviderSpec:
    """Resolve by stored canonical ``provider``; unknown ids fall back to OpenAI."""
    return _BY_ID.get(canonical_id, _DEFAULT_SPEC)


def canonical_provider_id(raw: str) -> str:
    """Map user/API input to the canonical ``provider`` string persisted in SQLite."""
    p = (raw or "").strip().lower()
    for spec in LLM_PROVIDER_SPECS:
        if p == spec.id or p in spec.aliases:
            return spec.id
    return _DEFAULT_SPEC.id


def defaults_for_canonical(canonical_id: str) -> tuple[str, str]:
    """``(default_base_url, default_model)`` for a canonical provider id."""
    s = get_spec_by_id(canonical_id)
    return s.default_base_url, s.default_model


def env_probe_order_rowless() -> tuple[str, ...]:
    """Env vars to try when no ``llm_settings`` row applies (order preserved, deduped)."""
    ordered: list[str] = []
    seen: set[str] = set()
    for spec in LLM_PROVIDER_SPECS:
        for name in spec.env_key_names:
            if name not in seen:
                seen.add(name)
                ordered.append(name)
    return tuple(ordered)


def all_registered_env_var_names() -> frozenset[str]:
    """Union of env var names all providers may use (e.g. ``any key configured`` checks)."""
    out: set[str] = set()
    for spec in LLM_PROVIDER_SPECS:
        out.update(spec.env_key_names)
    return frozenset(out)
