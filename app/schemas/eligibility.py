from typing import Literal

from app.schemas.common import APIModel
from app.schemas.health import HealthTopicOut
from app.schemas.profile import ProfileIn

RuleResult = Literal["PASS", "FAIL", "UNKNOWN"]
EligibilityStatus = Literal["ELIGIBLE", "POSSIBLY_ELIGIBLE", "NOT_ELIGIBLE"]


class ReasonOut(APIModel):
    rule: str
    result: RuleResult
    message: str


class EligibilityResultOut(APIModel):
    id: str
    title: str
    category: str
    status: EligibilityStatus
    reasons: list[ReasonOut]
    near_miss: str | None
    documents: list[str]
    official_url: str | None
    source_name: str | None
    last_verified: str | None
    verified: bool


class StatusCounts(APIModel):
    ELIGIBLE: int
    POSSIBLY_ELIGIBLE: int
    NOT_ELIGIBLE: int


class EligibilityCheckOut(APIModel):
    results: list[EligibilityResultOut]
    counts: StatusCounts
    health_topics: list[HealthTopicOut] = []
    health_disclaimer: str | None = None
    explanation: str
    explanation_source: Literal["ai", "template"]


class EligibilityCheckIn(ProfileIn):
    pass
