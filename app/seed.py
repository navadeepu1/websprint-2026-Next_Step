from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import HealthTopic, Opportunity

SEED_DIR = Path(__file__).resolve().parents[1] / "seed"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def database_is_empty(session: Session) -> bool:
    opportunities = session.scalar(select(func.count()).select_from(Opportunity)) or 0
    topics = session.scalar(select(func.count()).select_from(HealthTopic)) or 0
    return opportunities == 0 and topics == 0


def load_seed_data(session: Session, seed_dir: Path | None = None) -> None:
    directory = seed_dir or SEED_DIR
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    opportunities_path = directory / "opportunities.json"
    topics_path = directory / "health_topics.json"
    if opportunities_path.exists():
        records = json.loads(opportunities_path.read_text(encoding="utf-8"))
        for item in records:
            if session.get(Opportunity, item["id"]) is None:
                session.add(
                    Opportunity(
                        id=item["id"],
                        title=item["title"],
                        category=item["category"],
                        description=item["description"],
                        criteria=item.get("criteria") or {},
                        documents=item.get("documents") or [],
                        official_url=item.get("official_url"),
                        source_name=item.get("source_name"),
                        last_verified=_parse_dt(item.get("last_verified")),
                        verified=bool(item.get("verified", False)),
                        active=bool(item.get("active", True)),
                        updated_at=_parse_dt(item.get("updated_at")) or now,
                    )
                )
    if topics_path.exists():
        records = json.loads(topics_path.read_text(encoding="utf-8"))
        for item in records:
            if session.get(HealthTopic, item["id"]) is None:
                session.add(
                    HealthTopic(
                        id=item["id"],
                        title=item["title"],
                        summary=item["summary"],
                        warning_signs=item.get("warning_signs") or [],
                        when_to_seek_help=item.get("when_to_seek_help") or [],
                        source_url=item.get("source_url"),
                        last_verified=_parse_dt(item.get("last_verified")),
                        updated_at=_parse_dt(item.get("updated_at")) or now,
                    )
                )
    session.commit()
