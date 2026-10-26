from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.constants import HEALTH_DISCLAIMER
from app.models import HealthTopic
from app.schemas.health import HealthTopicOut


def to_out(row: HealthTopic) -> HealthTopicOut:
    return HealthTopicOut(
        id=row.id,
        title=row.title,
        summary=row.summary,
        warning_signs=list(row.warning_signs or []),
        when_to_seek_help=list(row.when_to_seek_help or []),
        source_url=row.source_url,
        last_verified=row.last_verified,
        updated_at=row.updated_at,
        disclaimer=HEALTH_DISCLAIMER,
    )


def list_topics(session: Session) -> list[HealthTopic]:
    return list(session.scalars(select(HealthTopic).order_by(HealthTopic.title.asc())).all())


def get_topic(session: Session, topic_id: str) -> HealthTopic | None:
    return session.get(HealthTopic, topic_id)


def search_topics(session: Session, query: str) -> list[HealthTopic]:
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    stmt = (
        select(HealthTopic)
        .where(
            or_(
                HealthTopic.title.like(pattern, escape="\\"),
                HealthTopic.summary.like(pattern, escape="\\"),
            )
        )
        .order_by(HealthTopic.title.asc())
    )
    return list(session.scalars(stmt).all())
