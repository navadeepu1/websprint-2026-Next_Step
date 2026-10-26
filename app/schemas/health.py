from datetime import datetime

from pydantic import Field, HttpUrl

from app.schemas.common import APIModel


class HealthTopicIn(APIModel):
    id: str = Field(..., min_length=3, max_length=80, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(..., min_length=1, max_length=150)
    summary: str = Field(..., min_length=1, max_length=800)
    warning_signs: list[str] = Field(default_factory=list)
    when_to_seek_help: list[str] = Field(default_factory=list)
    source_url: HttpUrl | None = None
    last_verified: datetime | None = None
    updated_at: datetime | None = None


class HealthTopicOut(APIModel):
    id: str
    title: str
    summary: str
    warning_signs: list[str]
    when_to_seek_help: list[str]
    source_url: str | None
    last_verified: datetime | None
    updated_at: datetime
    disclaimer: str
