"""Typed error contract for the API.

Every non-2xx response body has shape:
    { "error": { "code": str, "message": str, "detail": object } }

Routes raise `APIError(...)`; the registered handler renders the envelope.
Un-handled exceptions become a generic 500 with code=INTERNAL_ERROR so the
frontend never has to guess whether a response is JSON or not.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(message)

    @classmethod
    def not_found(cls, kind: str, key: str) -> "APIError":
        return cls(
            code=f"{kind.upper()}_NOT_FOUND",
            message=f"{kind} '{key}' not found",
            status_code=404,
            detail={"kind": kind, "key": key},
        )

    @classmethod
    def bad_request(cls, message: str, detail: dict[str, Any] | None = None) -> "APIError":
        return cls(code="BAD_REQUEST", message=message, status_code=400, detail=detail)

    @classmethod
    def rate_limited(cls, message: str, detail: dict[str, Any] | None = None) -> "APIError":
        return cls(code="RATE_LIMITED", message=message, status_code=429, detail=detail)


def _envelope(code: str, message: str, detail: dict[str, Any]) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "detail": detail}}


def register(app: FastAPI) -> None:
    @app.exception_handler(APIError)
    async def _handle_api_error(_: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.detail),
        )

    @app.exception_handler(Exception)
    async def _handle_uncaught(_: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled exception in request")
        return JSONResponse(
            status_code=500,
            content=_envelope(
                "INTERNAL_ERROR",
                "An unexpected error occurred.",
                {"type": type(exc).__name__},
            ),
        )
