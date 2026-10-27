from fastapi import APIRouter, Request

from app.constants import HEALTH_DISCLAIMER
from app.eligibility.types import EligibilityStatus
from app.schemas.eligibility import EligibilityCheckOut, StatusCounts
from app.schemas.health import HealthTopicOut
from app.schemas.profile import ProfileIn
from app.services.explainer import template_explanation
from app.services.ai import explain
from app.services.health_topics import list_topics, to_out as topic_out
from app.services.matching import evaluate_profile, profile_from_schema
from app.services.discovery import serialize_results

router = APIRouter()


@router.post("/eligibility/check", response_model=EligibilityCheckOut)
def check(payload: ProfileIn, request: Request) -> EligibilityCheckOut:
    session = request.app.state.session_factory()
    try:
        results = evaluate_profile(session, payload)
        health_topics: list[HealthTopicOut] = []
        disclaimer = None
        if "health" in payload.need:
            health_topics = [topic_out(row) for row in list_topics(session)]
            disclaimer = HEALTH_DISCLAIMER
        explanation = template_explanation(profile_from_schema(payload), results)
        prompt = (
            "Rewrite this eligibility summary in plain, respectful language. "
            "Do not add facts, guarantees, or medical advice:\n" + explanation
        )
        explanation, explanation_source = explain(prompt, explanation, session)
        counts = StatusCounts(
            ELIGIBLE=sum(1 for item in results if item.status == EligibilityStatus.ELIGIBLE),
            POSSIBLY_ELIGIBLE=sum(1 for item in results if item.status == EligibilityStatus.POSSIBLY_ELIGIBLE),
            NOT_ELIGIBLE=sum(1 for item in results if item.status == EligibilityStatus.NOT_ELIGIBLE),
        )
        return EligibilityCheckOut(
            results=serialize_results(results),
            counts=counts,
            health_topics=health_topics,
            health_disclaimer=disclaimer,
            explanation=explanation,
            explanation_source=explanation_source,
        )
    finally:
        session.close()
