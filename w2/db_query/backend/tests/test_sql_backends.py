"""Resolver + SQL guard behavior for pluggable backends."""

from db_query.adapters import infer_backend_id, resolve_backend
from db_query.services.sql_guard import prepare_select_sql


def test_infer_backend_id_postgres() -> None:
    assert infer_backend_id("postgresql://u:p@localhost:5432/db") == "postgres"
    assert infer_backend_id("postgres://u:p@localhost/db") == "postgres"


def test_infer_backend_id_mysql() -> None:
    assert infer_backend_id("mysql://root:pw@127.0.0.1:3306/app") == "mysql"
    assert infer_backend_id("mysql+pymysql://root:pw@127.0.0.1:3306/app") == "mysql"
    assert infer_backend_id("mariadb://root@localhost:3306/app") == "mysql"


def test_resolve_backend_url_scheme_wins_over_conflicting_hint() -> None:
    mysql = resolve_backend(
        connection_url="mysql://root:123456@127.0.0.1:3306/employee",
        backend_hint="postgres",
    )
    assert mysql.backend_id == "mysql"


def test_resolve_backend_uses_hint_when_scheme_unknown() -> None:
    mysql = resolve_backend(connection_url="jdbc:mysql://h:3306/d", backend_hint="mysql")
    assert mysql.backend_id == "mysql"


def test_prepare_select_mysql_dialect_roundtrip() -> None:
    sql, injected = prepare_select_sql("SELECT 1", 500, sqlglot_dialect="mysql")
    assert "1" in sql
    assert injected is True
    sql2, injected2 = prepare_select_sql("SELECT 2 LIMIT 10", 500, sqlglot_dialect="mysql")
    assert "10" in sql2
    assert injected2 is False
