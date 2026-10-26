from datetime import datetime

from pydantic import Field, field_validator, HttpUrl

from app.constants import CATEGORIES, EDUCATION_LEVELS, NEEDS, OCCUPATIONS
from app.schemas.common import APIModel


class Criteria(APIModel):
    min_age: int | None = Field(default=None, ge=0, le=120)
    max_age: int | None = Field(default=None, ge=0, le=120)
    education_levels: list[str] | None = None
    occupations: list[str] | None = None
    max_annual_income: int | None = Field(default=None, ge=0, le=100_000_000)
    states: list[str] | None = None
    needs: list[str] | None = None
    requires_land: bool | None = None
    disability_required: bool | None = None

    @field_validator("education_levels")
    @classmethod
    def validate_education_levels(cls, value: list[str] | None) -> list[str] | None:
        if not value:
            return value
        invalid = [item for item in value if item not in EDUCATION_LEVELS]
        if invalid:
            raise ValueError("education_levels contains an unsupported value.")
        return value

    @field_validator("occupations")
    @classmethod
    def validate_occupations(cls, value: list[str] | None) -> list[str] | None:
        if not value:
            return value
        invalid = [item for item in value if item not in OCCUPATIONS]
        if invalid:
            raise ValueError("occupations contains an unsupported value.")
        return value

    @field_validator("needs")
    @classmethod
    def validate_needs(cls, value: list[str] | None) -> list[str] | None:
        if not value:
            return value
        invalid = [item for item in value if item not in NEEDS]
        if invalid:
            raise ValueError("needs contains an unsupported value.")
        return value


class OpportunityIn(APIModel):
    id: str = Field(..., min_length=3, max_length=80, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(..., min_length=1, max_length=150)
    category: str
    description: str = Field(..., min_length=1, max_length=1000)
    criteria: Criteria
    documents: list[str] = Field(default_factory=list)
    official_url: HttpUrl | None = None
    source_name: str | None = Field(default=None, max_length=200)
    last_verified: datetime | None = None
    verified: bool = False
    active: bool = True
    updated_at: datetime | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in CATEGORIES:
            raise ValueError("category is not recognised.")
        return value

    @field_validator("documents")
    @classmethod
    def validate_documents(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        return cleaned


class OpportunityOut(APIModel):
    id: str
    title: str
    category: str
    description: str
    criteria: Criteria
    documents: list[str]
    official_url: str | None
    source_name: str | None
    last_verified: datetime | None
    verified: bool
    active: bool
    updated_at: datetime
