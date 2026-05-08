"""Tests for the LLM provider registry (extension point for new vendors)."""

from db_query.services.llm_provider_registry import (
    LLM_PROVIDER_SPECS,
    all_registered_env_var_names,
    canonical_provider_id,
    defaults_for_canonical,
    env_probe_order_rowless,
    get_spec_by_id,
    iter_provider_specs,
)


def test_iter_provider_specs_matches_tuple() -> None:
    assert iter_provider_specs() == LLM_PROVIDER_SPECS


def test_canonical_unknown_maps_to_openai() -> None:
    assert canonical_provider_id("totally-unknown-vendor") == "openai"


def test_get_spec_by_id_unknown_falls_back_openai() -> None:
    s = get_spec_by_id("nonexistent")
    assert s.id == "openai"


def test_defaults_for_canonical() -> None:
    o = defaults_for_canonical("openai")
    q = defaults_for_canonical("qwen")
    assert o[0].startswith("https://api.openai")
    assert "dashscope" in q[0]


def test_env_probe_rowless_dedupes_preserves_first_occurrence_order() -> None:
    order = env_probe_order_rowless()
    assert "OPENAI_API_KEY" in order and "DASHSCOPE_API_KEY" in order
    assert len(order) == len(set(order))


def test_all_registered_env_names_covers_specs() -> None:
    names = all_registered_env_var_names()
    for spec in LLM_PROVIDER_SPECS:
        for n in spec.env_key_names:
            assert n in names
