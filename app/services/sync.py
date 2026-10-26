import json
from datetime import datetime, timezone
from typing import Any

import httpx
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import HealthTopic, Opportunity, SyncLog
from app.schemas.health import HealthTopicIn
from app.schemas.opportunity import OpportunityIn


def _records(payload: Any) -> tuple[list[dict], list[dict]]:
    if isinstance(payload, list):
        return payload, []
    if not isinstance(payload, dict):
        raise ValueError("Source payload must be an array or an object.")
    return payload.get("opportunities", []), payload.get("health_topics", [])


def sync_source(session: Session, url: str, client: httpx.Client | None = None) -> SyncLog:
    settings = get_settings()
    started = datetime.now(timezone.utc).replace(tzinfo=None)
    log = SyncLog(source_url=url, started_at=started, status="running")
    session.add(log)
    session.flush()
    own_client = client is None
    http_client = client or httpx.Client(timeout=settings.sync_timeout_seconds, follow_redirects=True)
    upserted = rejected = 0
    try:
        response = http_client.get(url)
        response.raise_for_status()
        opportunities, topics = _records(response.json())
        for raw in opportunities:
            try:
                item = OpportunityIn.model_validate(raw)
            except ValidationError:
                rejected += 1
                continue
            existing = session.get(Opportunity, item.id)
            values = item.model_dump(mode="python", exclude_none=True)
            if item.official_url is not None:
                values["official_url"] = str(item.official_url)
            values["updated_at"] = item.updated_at or started
            if existing is None:
                session.add(Opportunity(**values))
            else:
                for key, value in values.items():
                    if key != "id" and value is not None:
                        setattr(existing, key, value)
            upserted += 1
        for raw in topics:
            try:
                item = HealthTopicIn.model_validate(raw)
            except ValidationError:
                rejected += 1
                continue
            existing = session.get(HealthTopic, item.id)
            values = item.model_dump(mode="python", exclude_none=True)
            if item.source_url is not None:
                values["source_url"] = str(item.source_url)
            values["updated_at"] = item.updated_at or started
            if existing is None:
                session.add(HealthTopic(**values))
            else:
                for key, value in values.items():
                    if key != "id" and value is not None:
                        setattr(existing, key, value)
            upserted += 1
        log.status = "success"
        log.records_upserted = upserted
        log.records_rejected = rejected
        log.finished_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.commit()
        return log
    except Exception as exc:
        session.rollback()
        failed = SyncLog(
            source_url=url,
            started_at=started,
            finished_at=datetime.now(timezone.utc).replace(tzinfo=None),
            status="failed",
            records_upserted=upserted,
            records_rejected=rejected,
            error_message=str(exc)[:1000],
        )
        session.add(failed)
        session.commit()
        raise
    finally:
        if own_client:
            http_client.close()


def sync_configured_sources(session: Session) -> list[SyncLog]:
    logs = []
    for url in get_settings().data_source_url_list():
        try:
            logs.append(sync_source(session, url))
        except Exception:
            failed = latest_sync(session)
            if failed is not None and failed.source_url == url:
                logs.append(failed)
    return logs


def latest_sync(session: Session) -> SyncLog | None:
    return session.scalar(select(SyncLog).order_by(SyncLog.finished_at.desc()).limit(1))
