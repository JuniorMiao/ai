"""Unit tests for LLM provider defaults and endpoint resolution."""

import sqlite3

import pytest

from db_query.services.llm_providers import (
    DASHSCOPE_COMPAT_BASE,
    OPENAI_DEFAULT_BASE,
    OPENAI_DEFAULT_MODEL,
    QWEN_DEFAULT_MODEL,
    defaults_for_provider,
    normalize_stored_provider,
    resolve_endpoint_for_row,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("openai", "openai"),
        ("Qwen", "qwen"),
        ("dashscope", "qwen"),
        ("alibaba", "qwen"),
        ("通义", "qwen"),
        ("unknown", "openai"),
        ("", "openai"),
    ],
)
def test_normalize_stored_provider(raw: str, expected: str) -> None:
    assert normalize_stored_provider(raw) == expected


def test_defaults_for_provider() -> None:
    assert defaults_for_provider("openai") == (OPENAI_DEFAULT_BASE, OPENAI_DEFAULT_MODEL)
    assert defaults_for_provider("qwen") == (DASHSCOPE_COMPAT_BASE, QWEN_DEFAULT_MODEL)


def _row(provider: str, base_url: str, model: str) -> sqlite3.Row:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE llm (provider TEXT, base_url TEXT, model TEXT)",
    )
    conn.execute(
        "INSERT INTO llm VALUES (?,?,?)",
        (provider, base_url, model),
    )
    return conn.execute("SELECT * FROM llm").fetchone()


def test_resolve_endpoint_for_row_none() -> None:
    base, model = resolve_endpoint_for_row(None)
    assert base == OPENAI_DEFAULT_BASE
    assert model == OPENAI_DEFAULT_MODEL


def test_resolve_endpoint_for_row_qwen_fills_defaults() -> None:
    base, model = resolve_endpoint_for_row(_row("qwen", "", ""))
    assert base == DASHSCOPE_COMPAT_BASE
    assert model == QWEN_DEFAULT_MODEL


def test_resolve_endpoint_for_row_qwen_custom() -> None:
    base, model = resolve_endpoint_for_row(
        _row("qwen", "https://custom.example/v1", "qwen-max"),
    )
    assert base == "https://custom.example/v1"
    assert model == "qwen-max"


def test_resolve_endpoint_for_row_openai_partial() -> None:
    base, model = resolve_endpoint_for_row(_row("openai", "", "gpt-4o"))
    assert base == OPENAI_DEFAULT_BASE
    assert model == "gpt-4o"
