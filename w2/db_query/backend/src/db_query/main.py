"""FastAPI entrypoint for db_query."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from db_query.api import dbs as dbs_router
from db_query.config import get_settings
from db_query.schemas.errors import ErrorDetail, ErrorResponse
from db_query.storage.sqlite import connect, init_schema, load_schema_sql


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    conn = connect(settings.sqlite_path)
    init_schema(conn, load_schema_sql())
    app.state.db = conn
    try:
        yield
    finally:
        conn.close()


app = FastAPI(title="db_query", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dbs_router.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _ = request
    body = ErrorResponse(
        error=ErrorDetail(code="internal_error", message=str(exc)),
    )
    return JSONResponse(
        status_code=500,
        content=body.model_dump(by_alias=True),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
