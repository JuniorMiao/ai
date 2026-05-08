"""PostgreSQL introspection: tables/views/columns as JSON for cache and NL context."""

from __future__ import annotations

from typing import Any

import psycopg


def fetch_schema_metadata(connection_url: str) -> dict[str, Any]:
    """Return tables/columns suitable for UI and LLM context."""
    out: dict[str, Any] = {"schemas": [], "tables": []}
    with psycopg.connect(connection_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_schema, table_name, table_type
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                  AND table_schema NOT LIKE 'pg_%'
                ORDER BY table_schema, table_name
                """
            )
            tables_meta = cur.fetchall()
            for schema, table, ttype in tables_meta:
                cur.execute(
                    """
                    SELECT
                      a.attname::text,
                      pg_catalog.format_type(a.atttypid, a.atttypmod),
                      NOT a.attnotnull AS col_nullable,
                      COALESCE(pg_catalog.col_description(a.attrelid, a.attnum), '')
                    FROM pg_catalog.pg_attribute a
                    JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
                    JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                    WHERE a.attnum > 0
                      AND NOT a.attisdropped
                      AND n.nspname = %s
                      AND c.relname = %s
                    ORDER BY a.attnum
                    """,
                    (schema, table),
                )
                cols = [
                    {
                        "name": r[0],
                        "dataType": r[1],
                        "nullable": bool(r[2]),
                        "comment": (r[3] or "").strip(),
                    }
                    for r in cur.fetchall()
                ]
                out["tables"].append(
                    {
                        "schema": schema,
                        "name": table,
                        "type": ttype,
                        "columns": cols,
                    }
                )
    out["schemas"] = sorted({t["schema"] for t in out["tables"]})
    return out
