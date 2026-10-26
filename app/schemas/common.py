from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorDetail(APIModel):
    field: str | None = None
    message: str


class ErrorBody(APIModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorEnvelope(APIModel):
    error: ErrorBody


class HealthStatusOut(APIModel):
    status: str
    database: str
    last_successful_sync: str | None
    ai_provider: str
    sync: str


class OpportunityFilters(APIModel):
    category: str | None = None
    verified: bool | None = None
    active: bool | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


def error_payload(code: str, message: str, details: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    parsed = [ErrorDetail(**item) for item in details or []]
    return ErrorEnvelope(error=ErrorBody(code=code, message=message, details=parsed)).model_dump()
