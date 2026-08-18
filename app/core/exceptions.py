"""Custom exception classes and FastAPI exception handlers.

All business exceptions inherit from AppError so handlers can be registered
centrally in main.py. HTTP status codes are declared on each exception class.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for all application-level exceptions."""

    status_code: int = 500
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, detail: str | None = None):
        self.message = message or self.default_message
        self.detail = detail
        super().__init__(self.message)


class UnauthorizedError(AppError):
    """401 — Missing or invalid authentication credentials."""

    status_code = 401
    default_message = "Authentication required."


class ForbiddenError(AppError):
    """403 — Authenticated but insufficient role/permissions."""

    status_code = 403
    default_message = "You do not have permission to perform this action."


class NotFoundError(AppError):
    """404 — Resource does not exist."""

    status_code = 404
    default_message = "The requested resource was not found."


class ConflictError(AppError):
    """409 — Conflicting state (e.g. duplicate application, already published)."""

    status_code = 409
    default_message = "A conflict occurred."


class BadRequestError(AppError):
    """400 — Invalid business operation (not a validation error)."""

    status_code = 400
    default_message = "Invalid request."


def _error_response(exc: AppError) -> JSONResponse:
    content: dict = {"error": exc.message}
    if exc.detail:
        content["detail"] = exc.detail
    return JSONResponse(status_code=exc.status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app."""

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedError):
        return _error_response(exc)

    @app.exception_handler(ForbiddenError)
    async def forbidden_handler(request: Request, exc: ForbiddenError):
        return _error_response(exc)

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return _error_response(exc)

    @app.exception_handler(ConflictError)
    async def conflict_handler(request: Request, exc: ConflictError):
        return _error_response(exc)

    @app.exception_handler(BadRequestError)
    async def bad_request_handler(request: Request, exc: BadRequestError):
        return _error_response(exc)

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        # Never expose internal stack traces to clients
        import logging
        logging.getLogger(__name__).exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "An internal server error occurred."},
        )
