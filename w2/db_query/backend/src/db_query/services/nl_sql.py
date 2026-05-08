"""Natural language → SQL using OpenAI-compatible Chat API (optional)."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from db_query.services.metadata import fetch_schema_metadata


def _schema_digest(metadata: dict[str, Any], max_chars: int = 12000) -> str:
    raw = json.dumps(metadata, ensure_ascii=False)
    if len(raw) <= max_chars:
        return raw
    return raw[:max_chars] + "\n... [truncated]"


def generate_sql_from_prompt(
    connection_url: str,
    prompt: str,
    *,
    model: str | None = None,
) -> tuple[str, list[str]]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set; configure it to use natural-language SQL generation."
        )

    md = fetch_schema_metadata(connection_url)
    digest = _schema_digest(md)
    sys_prompt = (
        "You are a PostgreSQL expert. Given schema JSON and a user question, "
        "reply with a single SELECT statement only, no markdown or commentary. "
        "Use only tables/columns present in the schema."
    )
    user_content = f"Schema (JSON):\n{digest}\n\nQuestion:\n{prompt}"

    client = OpenAI(api_key=api_key)
    used_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    resp = client.chat.completions.create(
        model=used_model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )
    choice = resp.choices[0].message.content or ""
    sql = choice.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines)
        sql = sql.strip()
    warnings: list[str] = []
    return sql, warnings
