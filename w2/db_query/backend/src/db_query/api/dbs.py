"""Database registration HTTP API (stub list; PUT/metadata/query in later tasks)."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1", tags=["dbs"])


@router.get("/dbs")
def list_databases(request: Request) -> list[dict[str, str | None]]:
    conn = request.app.state.db
    cur = conn.execute(
        "SELECT name, created_at, updated_at FROM registered_database ORDER BY name"
    )
    rows = cur.fetchall()
    return [
        {
            "name": r["name"],
            "createdAt": r["created_at"],
            "updatedAt": r["updated_at"],
        }
        for r in rows
    ]
