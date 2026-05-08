"""Smoke tests for FastAPI app."""

from fastapi.testclient import TestClient

from db_query.main import app


def test_health() -> None:
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


def test_list_dbs_empty() -> None:
    with TestClient(app) as client:
        res = client.get("/api/v1/dbs")
        assert res.status_code == 200
        assert res.json() == []
