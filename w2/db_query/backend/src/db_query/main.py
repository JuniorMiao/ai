"""FastAPI application factory (Phase 2 foundation): CORS, SQLite lifespan, unified errors."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from db_query.api import dbs as dbs_router
from db_query.config import get_settings
from db_query.schemas.errors import ErrorDetail, ErrorResponse
from db_query.storage.sqlite import open_app_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    conn = open_app_database(settings)
    app.state.db = conn
    try:
        yield
    finally:
        conn.close()


def _register_exception_handlers(app: FastAPI) -> None:
    """Return JSON ``{ error: { code, message } }`` (camelCase) for common failures."""

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        parts: list[str] = []
        for err in exc.errors():
            loc = ".".join(str(x) for x in err.get("loc", ()))
            msg = err.get("msg", "")
            parts.append(f"{loc}: {msg}" if loc else msg)
        message = "; ".join(parts) if parts else "Validation failed"
        body = ErrorResponse(error=ErrorDetail(code="validation_error", message=message))
        return JSONResponse(
            status_code=422,
            content=body.model_dump(by_alias=True),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, list | dict):
            message = str(detail)
        else:
            message = str(detail)
        code = f"http_{exc.status_code}"
        body = ErrorResponse(error=ErrorDetail(code=code, message=message))
        return JSONResponse(
            status_code=exc.status_code,
            content=body.model_dump(by_alias=True),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        body = ErrorResponse(
            error=ErrorDetail(code="internal_error", message=str(exc)),
        )
        return JSONResponse(
            status_code=500,
            content=body.model_dump(by_alias=True),
        )


def create_app() -> FastAPI:
    """Build FastAPI app (``uvicorn db_query.main:app``)."""
    application = FastAPI(title="db_query", lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(application)
    application.include_router(dbs_router.router)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app: FastAPI = create_app()
