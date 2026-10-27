from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select

from app.models import ApplicationTracker, Opportunity, SavedOpportunity, UserProfile
from app.schemas.citizen import (
    ApplicationIn,
    ApplicationOut,
    ApplicationUpdate,
    ProfileOut,
    SavedOpportunityOut,
)
from app.schemas.profile import ProfileIn
from app.services.auth import user_from_token
from app.services.opportunities import to_out

router = APIRouter()


def _current_user(request: Request, authorization: str | None):
    session = request.app.state.session_factory()
    user = user_from_token(session, authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else None)
    return session, user


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.get("/profile", response_model=ProfileOut)
def get_profile(request: Request, authorization: str | None = Header(default=None)) -> ProfileOut:
    session, user = _current_user(request, authorization)
    try:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        record = session.get(UserProfile, user.id)
        if record is None:
            raise HTTPException(status_code=404, detail="No saved profile yet.")
        return ProfileOut(**record.profile, updated_at=record.updated_at)
    finally:
        session.close()


@router.put("/profile", response_model=ProfileOut)
def save_profile(payload: ProfileIn, request: Request, authorization: str | None = Header(default=None)) -> ProfileOut:
    session, user = _current_user(request, authorization)
    try:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        now = _now()
        record = session.get(UserProfile, user.id)
        values = payload.model_dump()
        if record is None:
            record = UserProfile(user_id=user.id, profile=values, updated_at=now)
            session.add(record)
        else:
            record.profile = values
            record.updated_at = now
        session.commit()
        return ProfileOut(**values, updated_at=now)
    finally:
        session.close()


@router.get("/saved-opportunities", response_model=list[SavedOpportunityOut])
def list_saved(request: Request, authorization: str | None = Header(default=None)) -> list[SavedOpportunityOut]:
    session, user = _current_user(request, authorization)
    try:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        rows = session.scalars(
            select(SavedOpportunity).where(SavedOpportunity.user_id == user.id).order_by(SavedOpportunity.created_at.desc())
        ).all()
        result = []
        for row in rows:
            opportunity = session.get(Opportunity, row.opportunity_id)
            if opportunity is not None:
                result.append(SavedOpportunityOut(opportunity=to_out(opportunity), saved_at=row.created_at))
        return result
    finally:
        session.close()


@router.post("/saved-opportunities/{opportunity_id}", response_model=SavedOpportunityOut, status_code=201)
def save_opportunity(opportunity_id: str, request: Request, authorization: str | None = Header(default=None)) -> SavedOpportunityOut:
    session, user = _current_user(request, authorization)
    try:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        opportunity = session.get(Opportunity, opportunity_id)
        if opportunity is None:
            raise HTTPException(status_code=404, detail="Opportunity not found.")
        existing = session.scalar(select(SavedOpportunity).where(SavedOpportunity.user_id == user.id, SavedOpportunity.opportunity_id == opportunity_id))
        if existing is None:
            existing = SavedOpportunity(user_id=user.id, opportunity_id=opportunity_id, created_at=_now())
            session.add(existing)
            session.commit()
        return SavedOpportunityOut(opportunity=to_out(opportunity), saved_at=existing.created_at)
    finally:
        session.close()


@router.delete("/saved-opportunities/{opportunity_id}", status_code=204)
def remove_saved(opportunity_id: str, request: Request, authorization: str | None = Header(default=None)) -> None:
    session, user = _current_user(request, authorization)
    try:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        record = session.scalar(select(SavedOpportunity).where(SavedOpportunity.user_id == user.id, SavedOpportunity.opportunity_id == opportunity_id))
        if record is None:
            raise HTTPException(status_code=404, detail="Saved opportunity not found.")
        session.delete(record)
        session.commit()
    finally:
        session.close()


@router.get("/applications", response_model=list[ApplicationOut])
def list_applications(request: Request, authorization: str | None = Header(default=None)) -> list[ApplicationOut]:
    session, user = _current_user(request, authorization)
    try:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        rows = session.scalars(select(ApplicationTracker).where(ApplicationTracker.user_id == user.id).order_by(ApplicationTracker.updated_at.desc())).all()
        result = []
        for row in rows:
            opportunity = session.get(Opportunity, row.opportunity_id)
            if opportunity is not None:
                result.append(ApplicationOut(id=row.id, opportunity=to_out(opportunity), status=row.status, notes=row.notes, next_step=row.next_step, updated_at=row.updated_at))
        return result
    finally:
        session.close()


@router.post("/applications", response_model=ApplicationOut, status_code=201)
def create_application(payload: ApplicationIn, request: Request, authorization: str | None = Header(default=None)) -> ApplicationOut:
    session, user = _current_user(request, authorization)
    try:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        opportunity = session.get(Opportunity, payload.opportunity_id)
        if opportunity is None:
            raise HTTPException(status_code=404, detail="Opportunity not found.")
        existing = session.scalar(select(ApplicationTracker).where(ApplicationTracker.user_id == user.id, ApplicationTracker.opportunity_id == payload.opportunity_id))
        if existing is not None:
            raise HTTPException(status_code=409, detail="This opportunity is already in your tracker.")
        row = ApplicationTracker(user_id=user.id, opportunity_id=payload.opportunity_id, status=payload.status, notes=payload.notes, next_step=payload.next_step, updated_at=_now())
        session.add(row)
        session.commit()
        return ApplicationOut(id=row.id, opportunity=to_out(opportunity), status=row.status, notes=row.notes, next_step=row.next_step, updated_at=row.updated_at)
    finally:
        session.close()


@router.patch("/applications/{application_id}", response_model=ApplicationOut)
def update_application(application_id: int, payload: ApplicationUpdate, request: Request, authorization: str | None = Header(default=None)) -> ApplicationOut:
    session, user = _current_user(request, authorization)
    try:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required.")
        row = session.scalar(select(ApplicationTracker).where(ApplicationTracker.id == application_id, ApplicationTracker.user_id == user.id))
        if row is None:
            raise HTTPException(status_code=404, detail="Application tracker item not found.")
        changes = payload.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(row, key, value)
        row.updated_at = _now()
        session.commit()
        opportunity = session.get(Opportunity, row.opportunity_id)
        return ApplicationOut(id=row.id, opportunity=to_out(opportunity), status=row.status, notes=row.notes, next_step=row.next_step, updated_at=row.updated_at)
    finally:
        session.close()
