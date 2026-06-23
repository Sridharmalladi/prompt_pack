"""FastAPI application entry point."""

import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.routes import analyze as analyze_router
from app.api.routes import chat as chat_router
from app.core import errors as error_handlers
from app.core.config import settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup / shutdown hooks."""
    configure_logging(debug=settings.debug)
    logger.info("Data Science Buddy API starting up", version=settings.app_version)
    routes = [f"{m} {r.path}" for r in app.routes for m in getattr(r, "methods", [])]
    logger.info("Registered routes", routes=routes)
    yield
    logger.info("Data Science Buddy API shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Global exception handlers must be registered before routers
error_handlers.register(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router.router)
app.include_router(chat_router.router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: object) -> Response:
    """Attach a unique request ID to every inbound request for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    with logger.contextualize(request_id=request_id):
        response: Response = await call_next(request)  # type: ignore[arg-type]
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Liveness probe — returns ok when the service is up."""
    logger.debug("Health check called")
    return {"status": "ok", "version": settings.app_version}
