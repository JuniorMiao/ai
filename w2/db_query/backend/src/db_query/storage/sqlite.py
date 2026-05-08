"""SQLite connection and schema bootstrap."""

import sqlite3
from pathlib import Path


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection, schema_sql: str) -> None:
    conn.executescript(schema_sql)
    conn.commit()


def load_schema_sql() -> str:
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    return schema_path.read_text(encoding="utf-8")
