from typing import Literal

from pydantic import Field, field_validator

from app.config import get_settings
from app.constants import EDUCATION_LEVELS, NEEDS, OCCUPATIONS
from app.schemas.common import APIModel

EducationLevel = Literal[
    "none",
    "primary",
    "secondary",
    "12th",
    "diploma",
    "undergraduate",
    "postgraduate",
    "other",
]
Occupation = Literal[
    "student",
    "employed",
    "unemployed",
    "self_employed",
    "farmer",
    "retired",
    "homemaker",
    "other",
]
Need = Literal["study", "work", "health", "farming", "retirement_support"]


class ProfileIn(APIModel):
    age: int = Field(..., description="Age in years")
    education_level: EducationLevel
    occupation: Occupation
    annual_income: int
    state: str
    need: list[Need] = Field(..., min_length=1, max_length=5)
    has_land: bool | None = None
    has_disability: bool | None = None

    @field_validator("age")
    @classmethod
    def validate_age(cls, value: int) -> int:
        if value < 0 or value > 120:
            raise ValueError("Age must be between 0 and 120.")
        return value

    @field_validator("annual_income")
    @classmethod
    def validate_income(cls, value: int) -> int:
        if value < 0 or value > 100_000_000:
            raise ValueError("Annual income must be between 0 and 100,000,000.")
        return value

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        code = value.strip().upper()
        allowed = get_settings().allowed_state_list()
        if code not in allowed:
            raise ValueError(f"State must be one of: {', '.join(allowed)}.")
        return code

    @field_validator("need")
    @classmethod
    def validate_need(cls, value: list[Need]) -> list[Need]:
        if len(value) != len(set(value)):
            raise ValueError("Need values must be unique.")
        unknown = [item for item in value if item not in NEEDS]
        if unknown:
            raise ValueError("Need contains an unsupported value.")
        return value

    @field_validator("education_level")
    @classmethod
    def validate_education(cls, value: str) -> str:
        if value not in EDUCATION_LEVELS:
            raise ValueError("Education level is not recognised.")
        return value

    @field_validator("occupation")
    @classmethod
    def validate_occupation(cls, value: str) -> str:
        if value not in OCCUPATIONS:
            raise ValueError("Occupation is not recognised.")
        return value
