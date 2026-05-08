"""Execute validated SELECT against PostgreSQL."""

from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import tuple_row


def run_select(connection_url: str, sql: str) -> tuple[list[str], list[tuple[Any, ...]]]:
    with psycopg.connect(connection_url, row_factory=tuple_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description:
                columns = [d.name for d in cur.description]
            else:
                columns = []
            rows = list(cur.fetchall())
    return columns, rows
