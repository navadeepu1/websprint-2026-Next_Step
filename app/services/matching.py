from app.eligibility.engine import evaluate_all
from app.eligibility.types import EligibilityResult, Profile
from app.models import Opportunity
from app.schemas.profile import ProfileIn
from app.services.opportunities import all_active_opportunities


def profile_from_schema(payload: ProfileIn) -> Profile:
    return Profile(
        age=payload.age,
        education_level=payload.education_level,
        occupation=payload.occupation,
        annual_income=payload.annual_income,
        state=payload.state,
        need=list(payload.need),
        has_land=payload.has_land,
        has_disability=payload.has_disability,
    )


def opportunity_to_dict(row: Opportunity) -> dict:
    last_verified = row.last_verified.isoformat() if row.last_verified else None
    return {
        "id": row.id,
        "title": row.title,
        "category": row.category,
        "criteria": row.criteria or {},
        "documents": list(row.documents or []),
        "official_url": row.official_url,
        "source_name": row.source_name,
        "last_verified": last_verified,
        "verified": row.verified,
    }


def evaluate_profile(session, payload: ProfileIn) -> list[EligibilityResult]:
    profile = profile_from_schema(payload)
    records = [opportunity_to_dict(row) for row in all_active_opportunities(session)]
    return evaluate_all(profile, records)
