from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from app.schemas.common import error_payload
from app.schemas.health import HealthTopicOut
from app.services.health_topics import get_topic, list_topics, search_topics, to_out

router = APIRouter()


@router.get("/health-topics", response_model=list[HealthTopicOut])
def list_items(request: Request) -> list[HealthTopicOut]:
    session = request.app.state.session_factory()
    try:
        return [to_out(row) for row in list_topics(session)]
    finally:
        session.close()


@router.get("/health-topics/search", response_model=list[HealthTopicOut])
def search_items(request: Request, q: str = Query(..., min_length=2, max_length=100)) -> list[HealthTopicOut]:
    session = request.app.state.session_factory()
    try:
        return [to_out(row) for row in search_topics(session, q)]
    finally:
        session.close()


@router.get("/health-topics/{topic_id}", response_model=HealthTopicOut)
def get_item(topic_id: str, request: Request) -> JSONResponse:
    session = request.app.state.session_factory()
    try:
        row = get_topic(session, topic_id)
        if row is None:
            return JSONResponse(
                status_code=404,
                content=error_payload("not_found", "Health topic not found.", [{"field": "id", "message": "Health topic not found."}]),
            )
        return JSONResponse(content=to_out(row).model_dump(mode="json"))
    finally:
        session.close()
