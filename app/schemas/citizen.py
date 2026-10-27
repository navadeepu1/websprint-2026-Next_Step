from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.common import APIModel
from app.schemas.eligibility import EligibilityResultOut
from app.schemas.opportunity import OpportunityOut
from app.schemas.profile import ProfileIn


class ProfileOut(ProfileIn):
    updated_at: datetime


class SavedOpportunityOut(APIModel):
    opportunity: OpportunityOut
    saved_at: datetime


ApplicationStatus = Literal["interested", "preparing", "submitted", "in_review", "completed", "closed"]


class ApplicationIn(APIModel):
    opportunity_id: str = Field(..., min_length=1, max_length=80)
    status: ApplicationStatus = "interested"
    notes: str = Field(default="", max_length=2000)
    next_step: str = Field(default="", max_length=300)


class ApplicationUpdate(APIModel):
    status: ApplicationStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)
    next_step: str | None = Field(default=None, max_length=300)


class ApplicationOut(APIModel):
    id: int
    opportunity: OpportunityOut
    status: ApplicationStatus
    notes: str
    next_step: str
    updated_at: datetime


class DiscoverySection(APIModel):
    category: str
    title: str
    count: int
    opportunities: list[EligibilityResultOut]


class DiscoveryOut(APIModel):
    profile: ProfileOut
    total_matches: int
    sections: list[DiscoverySection]
