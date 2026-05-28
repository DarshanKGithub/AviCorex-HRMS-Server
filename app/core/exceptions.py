from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

class APIException(Exception):
    def __init__(self, status_code: int, error_code: str, detail: str):
        self.status_code = status_code
        self.error_code = error_code
        self.detail = detail

def setup_exception_handlers(app):
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_code": exc.error_code, "detail": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "VALIDATION_ERROR",
                "detail": "Invalid request parameters",
                "errors": exc.errors()
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception during request to {request.url.path}")
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_SERVER_ERROR",
                "detail": "An unexpected error occurred. Please try again later."
            },
        )
