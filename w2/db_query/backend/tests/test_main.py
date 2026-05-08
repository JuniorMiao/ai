"""Smoke tests for FastAPI app."""

from fastapi.testclient import TestClient

from db_query.main import app


def test_health() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


def test_list_dbs_json_array() -> None:
    with TestClient(app) as client:
        res = client.get("/api/v1/dbs")
        assert res.status_code == 200
        body = res.json()
        assert isinstance(body, list)
        if body:
            assert "name" in body[0]


def test_delete_unknown_database_returns_404() -> None:
    with TestClient(app) as client:
        res = client.delete("/api/v1/dbs/__missing_connection_xyz__")
        assert res.status_code == 404
        assert res.json()["error"]["code"] == "http_404"


def test_not_found_uses_unified_error_shape() -> None:
    with TestClient(app) as client:
        res = client.get("/__no_such_route__")
        assert res.status_code == 404
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] == "http_404"
        assert "message" in data["error"]
