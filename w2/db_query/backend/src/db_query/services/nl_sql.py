"""Natural language → SQL using OpenAI-compatible Chat API."""

from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI


def _schema_digest(metadata: dict[str, Any], max_chars: int = 12000) -> str:
    raw = json.dumps(metadata, ensure_ascii=False)
    if len(raw) <= max_chars:
        return raw
    return raw[:max_chars] + "\n... [truncated]"


def generate_sql_from_prompt(
    metadata: dict[str, Any],
    prompt: str,
    *,
    base_url: str,
    api_key: str,
    model: str,
) -> tuple[str, list[str]]:
    """Call chat completions with schema JSON context; return raw SQL text + warnings."""
    digest = _schema_digest(metadata)
    sys_prompt = (
        "You translate questions into PostgreSQL SELECT queries.\n"
        "Rules:\n"
        "- Output exactly one SELECT statement. No markdown fences, no prose.\n"
        "- Use only tables, views, and columns that appear in the provided schema JSON.\n"
        "- Prefer explicit column lists over SELECT * unless the question asks for all columns.\n"
        "- Use sensible aliases and ISO timestamp/date literals where appropriate.\n"
        "- Do not use DDL, DML, or multiple statements.\n"
    )
    user_content = f"Schema (JSON):\n{digest}\n\nQuestion:\n{prompt.strip()}"

    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
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
        inner = re.match(r"^sql\s*", sql, flags=re.IGNORECASE)
        if inner:
            sql = sql[inner.end() :].strip()
    warnings: list[str] = []
    return sql, warnings
