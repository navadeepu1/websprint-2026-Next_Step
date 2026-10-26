from fastapi import APIRouter, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SyncLog
from app.schemas.common import HealthStatusOut

router = APIRouter()


@router.get("/health", response_model=HealthStatusOut)
def health(request: Request) -> HealthStatusOut:
    session: Session = request.app.state.session_factory()
    try:
        session.execute(select(1))
        database = "ok"
        last = session.scalar(
            select(SyncLog)
            .where(SyncLog.status == "success")
            .order_by(SyncLog.finished_at.desc())
        )
        last_successful = last.finished_at.isoformat() if last and last.finished_at else None
        sync_status = request.app.state.sync_status
    except Exception:
        database = "error"
        last_successful = None
        sync_status = "unavailable"
    finally:
        session.close()
    overall = "ok" if database == "ok" else "degraded"
    return HealthStatusOut(
        status=overall,
        database=database,
        last_successful_sync=last_successful,
        ai_provider=request.app.state.settings.ai_provider,
        sync=sync_status,
    )
