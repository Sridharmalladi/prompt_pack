"""Global FastAPI exception handlers and error response helpers.

All error responses from this service use the shape:
  { "error": str, "code": str, "where": str }

This module registers handlers for:
  - Pydantic/FastAPI RequestValidationError  →  422
  - anthropic.RateLimitError                →  429
  - Unhandled Python exceptions             →  500
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger

import anthropic


def _error_body(error: str, code: str, where: str) -> dict:
    return {"error": error, "code": code, "where": where}


def register(app: FastAPI) -> None:
    """Attach all global exception handlers to the FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Reformat FastAPI's default 422 to our standard envelope."""
        msgs = "; ".join(
            f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}"
            for e in exc.errors()
        )
        logger.warning(
            "Request validation error",
            path=request.url.path,
            detail=msgs,
            request_id=getattr(request.state, "request_id", "—"),
        )
        return JSONResponse(
            status_code=422,
            content=_error_body(msgs, "VALIDATION_ERROR", "request"),
        )

    @app.exception_handler(anthropic.RateLimitError)
    async def rate_limit_handler(
        request: Request, exc: anthropic.RateLimitError
    ) -> JSONResponse:
        """Surface Anthropic rate-limit errors as 429 with our envelope."""
        logger.warning(
            "Anthropic rate limit hit",
            path=request.url.path,
            request_id=getattr(request.state, "request_id", "—"),
        )
        return JSONResponse(
            status_code=429,
            content=_error_body(
                "Anthropic API rate limit reached — please retry in a moment.",
                "RATE_LIMIT",
                "anthropic",
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all: log the full traceback and return a 500."""
        logger.exception(
            "Unhandled exception",
            path=request.url.path,
            request_id=getattr(request.state, "request_id", "—"),
        )
        return JSONResponse(
            status_code=500,
            content=_error_body(
                "An unexpected error occurred.",
                "INTERNAL_ERROR",
                "server",
            ),
        )
