import json
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select

from app.config import get_settings
from app.models import AuditLog, HealthTopic, Opportunity
from app.schemas.health import HealthTopicIn
from app.schemas.opportunity import OpportunityIn
from app.services.sync import sync_configured_sources

router = APIRouter(prefix="/admin")


def _authorize(request: Request, key: str | None) -> None:
    expected = get_settings().admin_api_key
    if not expected or key != expected:
        raise HTTPException(status_code=401, detail="Admin authentication required.")


def _audit(request: Request, action: str, resource: str, detail: str = "") -> None:
    session = request.app.state.session_factory()
    try:
        session.add(AuditLog(action=action, resource=resource, actor="admin", detail=detail[:2000], created_at=datetime.now(timezone.utc).replace(tzinfo=None)))
        session.commit()
    finally:
        session.close()


@router.post("/sync")
def run_sync(request: Request, x_admin_api_key: str | None = Header(default=None)):
    _authorize(request, x_admin_api_key)
    session = request.app.state.session_factory()
    try:
        logs = sync_configured_sources(session)
        _audit(request, "sync", "configured_sources", json.dumps({"count": len(logs)}))
        return [{"url": log.source_url, "status": log.status, "records_upserted": log.records_upserted, "records_rejected": log.records_rejected} for log in logs]
    finally:
        session.close()


@router.put("/opportunities/{item_id}")
def upsert_opportunity(item_id: str, payload: OpportunityIn, request: Request, x_admin_api_key: str | None = Header(default=None)):
    _authorize(request, x_admin_api_key)
    if payload.id != item_id:
        raise HTTPException(status_code=422, detail="Path id and payload id must match.")
    session = request.app.state.session_factory()
    try:
        values = payload.model_dump(mode="python", exclude_none=True)
        values["updated_at"] = payload.updated_at or datetime.now(timezone.utc).replace(tzinfo=None)
        item = session.get(Opportunity, item_id)
        if item is None:
            item = Opportunity(**values)
            session.add(item)
        else:
            for key, value in values.items():
                if key != "id":
                    setattr(item, key, value)
        session.commit()
        _audit(request, "upsert", f"opportunity:{item_id}")
        return {"id": item_id, "status": "saved"}
    finally:
        session.close()


@router.delete("/opportunities/{item_id}")
def deactivate_opportunity(item_id: str, request: Request, x_admin_api_key: str | None = Header(default=None)):
    _authorize(request, x_admin_api_key)
    session = request.app.state.session_factory()
    try:
        item = session.get(Opportunity, item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Opportunity not found.")
        item.active = False
        session.commit()
        _audit(request, "deactivate", f"opportunity:{item_id}")
        return {"id": item_id, "status": "deactivated"}
    finally:
        session.close()


@router.put("/health-topics/{item_id}")
def upsert_health_topic(item_id: str, payload: HealthTopicIn, request: Request, x_admin_api_key: str | None = Header(default=None)):
    _authorize(request, x_admin_api_key)
    if payload.id != item_id:
        raise HTTPException(status_code=422, detail="Path id and payload id must match.")
    session = request.app.state.session_factory()
    try:
        values = payload.model_dump(mode="python", exclude_none=True)
        values["updated_at"] = payload.updated_at or datetime.now(timezone.utc).replace(tzinfo=None)
        item = session.get(HealthTopic, item_id)
        if item is None:
            session.add(HealthTopic(**values))
        else:
            for key, value in values.items():
                if key != "id":
                    setattr(item, key, value)
        session.commit()
        _audit(request, "upsert", f"health_topic:{item_id}")
        return {"id": item_id, "status": "saved"}
    finally:
        session.close()
