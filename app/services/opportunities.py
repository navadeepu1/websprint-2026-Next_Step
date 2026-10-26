from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Opportunity
from app.schemas.opportunity import Criteria, OpportunityOut


def to_out(row: Opportunity) -> OpportunityOut:
    return OpportunityOut(
        id=row.id,
        title=row.title,
        category=row.category,
        description=row.description,
        criteria=Criteria.model_validate(row.criteria or {}),
        documents=list(row.documents or []),
        official_url=row.official_url,
        source_name=row.source_name,
        last_verified=row.last_verified,
        verified=row.verified,
        active=row.active,
        updated_at=row.updated_at,
    )


def list_opportunities(
    session: Session,
    *,
    category: str | None = None,
    verified: bool | None = None,
    active: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> Sequence[Opportunity]:
    stmt = select(Opportunity).order_by(Opportunity.title.asc())
    if category is not None:
        stmt = stmt.where(Opportunity.category == category)
    if verified is not None:
        stmt = stmt.where(Opportunity.verified == verified)
    if active is not None:
        stmt = stmt.where(Opportunity.active == active)
    return session.scalars(stmt.offset(offset).limit(limit)).all()


def get_opportunity(session: Session, opportunity_id: str) -> Opportunity | None:
    return session.get(Opportunity, opportunity_id)


def all_active_opportunities(session: Session) -> list[Opportunity]:
    return list(session.scalars(select(Opportunity).where(Opportunity.active.is_(True))).all())
