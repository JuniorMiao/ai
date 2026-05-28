"""MySQL / MariaDB introspection + read-only SELECT via PyMySQL."""

from __future__ import annotations

from typing import Any, ClassVar
from urllib.parse import unquote, urlparse

import pymysql

from db_query.adapters.base import SqlBackendAdapter
from db_query.adapters.registry import register_backend


def _connect_kwargs(connection_url: str) -> dict[str, Any]:
    p = urlparse(connection_url.strip())
    scheme = p.scheme.lower()
    if scheme not in ("mysql", "mysql+pymysql", "mariadb"):
        raise ValueError(f"Not a MySQL-compatible URL (scheme={scheme!r})")
    user = unquote(p.username) if p.username else ""
    password = unquote(p.password) if p.password else ""
    host = p.hostname or "localhost"
    port = int(p.port or 3306)
    path = (p.path or "").lstrip("/")
    database = path.split("/")[0] if path else ""
    if not database:
        raise ValueError("MySQL URL must include a database name in the path, e.g. mysql://u:p@host:3306/mydb")
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.Cursor,
    }


@register_backend("mysql")
class MysqlBackend(SqlBackendAdapter):
    backend_id: ClassVar[str] = "mysql"
    sqlglot_dialect: ClassVar[str] = "mysql"

    def llm_dialect_label(self) -> str:
        return "MySQL"

    def llm_dialect_rules(self) -> str:
        return (
            "- Use MySQL dialect syntax (backtick-quote reserved identifiers when needed).\n"
            "- The schema field in JSON is the MySQL database name; qualify as db.table "
            "when multiple databases appear.\n"
        )

    def fetch_schema_metadata(self, connection_url: str) -> dict[str, Any]:
        out: dict[str, Any] = {"schemas": [], "tables": []}
        kw = _connect_kwargs(connection_url)
        conn_kw = {k: v for k, v in kw.items() if k != "cursorclass"}
        with pymysql.connect(**conn_kw) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_schema, table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema NOT IN (
                        'information_schema', 'mysql', 'performance_schema', 'sys'
                    )
                    ORDER BY table_schema, table_name
                    """
                )
                tables_meta = cur.fetchall()
                for schema, table, ttype in tables_meta:
                    cur.execute(
                        """
                        SELECT column_name, column_type, is_nullable, column_comment
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position
                        """,
                        (schema, table),
                    )
                    cols = [
                        {
                            "name": r[0],
                            "dataType": r[1],
                            "nullable": (r[2] or "").upper() == "YES",
                            "comment": (r[3] or "").strip() if r[3] else "",
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
        kw = _connect_kwargs(connection_url)
        conn_kw = {k: v for k, v in kw.items() if k != "cursorclass"}
        with pymysql.connect(**conn_kw) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                desc = cur.description
                columns = [d[0] for d in desc] if desc else []
                rows = list(cur.fetchall())
        return columns, rows
