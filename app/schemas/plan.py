from app.schemas.common import APIModel
from app.schemas.profile import ProfileIn


class PlanRequest(ProfileIn):
    pass


class ChecklistItem(APIModel):
    order: int
    text: str
    opportunity_id: str | None = None


class PlanOut(APIModel):
    checklist: list[ChecklistItem]
    documents: list[str]
    links: list[dict[str, str | None]]
    warnings: list[str]
    explanation: str
    explanation_source: str
