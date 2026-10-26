from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import error_payload

FIELD_MESSAGES = {
    "age": "Age must be between 0 and 120.",
    "annual_income": "Annual income must be between 0 and 100,000,000.",
}


def _detail_from_error(err: dict) -> dict[str, str | None]:
    loc = [str(part) for part in err.get("loc", []) if part != "body"]
    field = loc[-1] if loc else None
    message = str(err.get("msg", "Invalid value"))
    if message.startswith("Value error, "):
        message = message.removeprefix("Value error, ")
    if field in FIELD_MESSAGES and err.get("type") in {"greater_than_equal", "less_than_equal"}:
        message = FIELD_MESSAGES[field]
    return {"field": field, "message": message}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [_detail_from_error(err) for err in exc.errors()]
        message = details[0]["message"] if details else "Request validation failed."
        return JSONResponse(
            status_code=422,
            content=error_payload("validation_error", message, details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(code, str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=error_payload("internal_error", "An unexpected error occurred."),
        )
