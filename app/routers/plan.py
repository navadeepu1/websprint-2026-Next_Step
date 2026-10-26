from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app.schemas.profile import ProfileIn
from app.services.explainer import template_explanation
from app.services.matching import evaluate_profile, profile_from_schema
from app.services.plan import build_plan, plan_to_markdown

router = APIRouter()


@router.post("/plan")
def create_plan(
    payload: ProfileIn,
    request: Request,
    format: str = Query(default="json", pattern="^(json|markdown)$"),
):
    session = request.app.state.session_factory()
    try:
        results = evaluate_profile(session, payload)
        profile = profile_from_schema(payload)
        explanation = template_explanation(profile, results)
        plan = build_plan(profile, results, explanation, "template")
        if format == "markdown":
            return PlainTextResponse(plan_to_markdown(plan), media_type="text/markdown")
        return JSONResponse(content=plan.model_dump())
    finally:
        session.close()
