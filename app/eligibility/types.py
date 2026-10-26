from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RuleResult(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class EligibilityStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    POSSIBLY_ELIGIBLE = "POSSIBLY_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


@dataclass(frozen=True)
class Profile:
    age: int
    education_level: str
    occupation: str
    annual_income: int
    state: str
    need: list[str]
    has_land: bool | None = None
    has_disability: bool | None = None


@dataclass(frozen=True)
class RuleOutcome:
    rule: str
    result: RuleResult
    message: str
    near_miss: str | None = None


@dataclass
class EligibilityResult:
    id: str
    title: str
    category: str
    status: EligibilityStatus
    reasons: list[RuleOutcome]
    near_miss: str | None
    documents: list[str]
    official_url: str | None
    source_name: str | None
    last_verified: str | None
    verified: bool
    criteria: dict[str, Any] = field(default_factory=dict)
