import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)

from src.pipeline import ModelOutputError


logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """Register safe public responses for processing failures."""

    @app.exception_handler(RequestValidationError)
    async def handle_invalid_request(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": (
                    "Invalid request. Provide only ticket_text as a non-empty "
                    "string with a maximum length of 12000 characters."
                )
            },
        )

    async def handle_processing_error(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        if isinstance(exc, APITimeoutError):
            status_code = 504
            detail = "Model provider timed out."

        elif isinstance(exc, RateLimitError):
            status_code = 503
            detail = (
                "Model provider is unavailable due to rate or quota limits."
            )

        elif isinstance(exc, (AuthenticationError, PermissionDeniedError)):
            status_code = 503
            detail = "Model provider access is unavailable."

        elif isinstance(exc, APIConnectionError):
            status_code = 503
            detail = "Could not connect to the model provider."

        elif isinstance(exc, APIStatusError):
            status_code = 502
            detail = "Model provider returned an unsuccessful response."

        elif isinstance(exc, ModelOutputError):
            status_code = 502
            detail = "Model provider returned an invalid ticket result."

        else:
            status_code = 500
            detail = "Internal processing error."

        # Avoid logging ticket content or raw provider error messages.
        logger.warning(
            "API processing failure: type=%s status=%s",
            type(exc).__name__,
            status_code,
        )

        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
        )

    for exception_type in (
        APITimeoutError,
        RateLimitError,
        AuthenticationError,
        PermissionDeniedError,
        APIConnectionError,
        APIStatusError,
        ModelOutputError,
        Exception,
    ):
        app.add_exception_handler(
            exception_type,
            handle_processing_error,
        )
