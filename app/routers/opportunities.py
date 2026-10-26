import hashlib
import json

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, Response

from app.constants import CATEGORIES
from app.schemas.common import error_payload
from app.schemas.opportunity import OpportunityOut
from app.services.opportunities import get_opportunity, list_opportunities, to_out

router = APIRouter()


@router.get("/opportunities", response_model=list[OpportunityOut])
def list_items(
    request: Request,
    category: str | None = Query(default=None),
    verified: bool | None = Query(default=None),
    active: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> JSONResponse:
    if category is not None and category not in CATEGORIES:
        return JSONResponse(
            status_code=422,
            content=error_payload("validation_error", "category is not recognised.", [{"field": "category", "message": "category is not recognised."}]),
        )
    session = request.app.state.session_factory()
    try:
        rows = list_opportunities(
            session,
            category=category,
            verified=verified,
            active=active,
            limit=limit,
            offset=offset,
        )
        payload = [to_out(row).model_dump(mode="json") for row in rows]
    finally:
        session.close()
    etag = hashlib.md5(json.dumps(payload, sort_keys=True, default=str).encode("utf-8"), usedforsecurity=False).hexdigest()
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": "max-age=300"})
    return JSONResponse(content=payload, headers={"ETag": etag, "Cache-Control": "max-age=300"})


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityOut)
def get_item(opportunity_id: str, request: Request) -> JSONResponse:
    session = request.app.state.session_factory()
    try:
        row = get_opportunity(session, opportunity_id)
        if row is None:
            return JSONResponse(
                status_code=404,
                content=error_payload("not_found", "Opportunity not found.", [{"field": "id", "message": "Opportunity not found."}]),
            )
        return JSONResponse(content=to_out(row).model_dump(mode="json"))
    finally:
        session.close()
