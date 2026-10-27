from collections import OrderedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.eligibility.types import EligibilityStatus
from app.models import Opportunity
from app.schemas.eligibility import EligibilityResultOut, ReasonOut
from app.schemas.profile import ProfileIn
from app.services.matching import evaluate_profile

CATEGORY_TITLES = {
    "scholarship": "Scholarships",
    "internship": "Internships",
    "job": "Jobs and placements",
    "training": "Training and skill building",
    "farmer_scheme": "Farmer schemes",
    "senior_support": "Senior support",
}


def serialize_results(results) -> list[EligibilityResultOut]:
    return [
        EligibilityResultOut(
            id=item.id,
            title=item.title,
            category=item.category,
            status=item.status.value,
            reasons=[ReasonOut(rule=reason.rule, result=reason.result.value, message=reason.message) for reason in item.reasons],
            near_miss=item.near_miss,
            documents=item.documents,
            official_url=item.official_url,
            source_name=item.source_name,
            last_verified=item.last_verified,
            verified=item.verified,
        )
        for item in results
    ]


def discover(session: Session, profile: ProfileIn):
    results = evaluate_profile(session, profile)
    eligible = [item for item in results if item.status != EligibilityStatus.NOT_ELIGIBLE]
    grouped = OrderedDict()
    for item in eligible:
        grouped.setdefault(item.category, []).append(item)
    return [
        (category, CATEGORY_TITLES.get(category, category.replace("_", " ").title()), items)
        for category, items in grouped.items()
    ]
