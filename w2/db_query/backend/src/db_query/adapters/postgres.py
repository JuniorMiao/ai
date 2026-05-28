"""PostgreSQL introspection + read-only SELECT via psycopg."""

from __future__ import annotations

from typing import Any, ClassVar

import psycopg
from psycopg.rows import tuple_row

from db_query.adapters.base import SqlBackendAdapter
from db_query.adapters.registry import register_backend
from db_query.adapters.url_utils import postgres_driver_url


@register_backend("postgres")
class PostgresBackend(SqlBackendAdapter):
    backend_id: ClassVar[str] = "postgres"
    sqlglot_dialect: ClassVar[str] = "postgres"

    def llm_dialect_label(self) -> str:
        return "PostgreSQL"

    def llm_dialect_rules(self) -> str:
        return (
            "- Use PostgreSQL syntax (identifiers case-fold unless double-quoted).\n"
            "- Respect search_path-visible schemas reflected in the JSON.\n"
        )

    def fetch_schema_metadata(self, connection_url: str) -> dict[str, Any]:
        out: dict[str, Any] = {"schemas": [], "tables": []}
        dsn = postgres_driver_url(connection_url)
        with psycopg.connect(dsn) as conn:
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

    def execute_select(
        self, connection_url: str, sql: str
    ) -> tuple[list[str], list[tuple[Any, ...]]]:
        dsn = postgres_driver_url(connection_url)
        with psycopg.connect(dsn, row_factory=tuple_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                if cur.description:
                    columns = [d.name for d in cur.description]
                else:
                    columns = []
                rows = list(cur.fetchall())
        return columns, rows
