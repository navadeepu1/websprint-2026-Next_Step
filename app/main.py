from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import Base, make_engine, make_session_factory
from app.errors import register_error_handlers
from app.middleware import install_request_guards
from app.routers import admin, auth, chat, citizen, eligibility, health, health_topics, opportunities, plan
from app.seed import load_seed_data
from app.services.sync import sync_configured_sources
from app.models import User
from app.services.auth import hash_password
from datetime import datetime, timezone
from sqlalchemy import select


def _apply_security_headers(app: FastAPI) -> None:
    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; connect-src 'self'; img-src 'self' data:; "
            "style-src 'self'; script-src 'self'; font-src 'self'"
        )
        return response


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        engine = make_engine(settings.database_url)
        Base.metadata.create_all(engine)
        factory = make_session_factory(engine)
        session = factory()
        try:
            load_seed_data(session)
            if session.scalar(select(User).where(User.email == "demo@nextstep.local")) is None:
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                session.add(User(email="demo@nextstep.local", display_name="Demo Citizen", password_hash=hash_password("Demo@12345"), created_at=now))
                session.add(User(email="student@nextstep.local", display_name="Student Demo", password_hash=hash_password("Student@12345"), created_at=now))
                session.commit()
            if settings.sync_on_start:
                try:
                    sync_configured_sources(session)
                    app.state.sync_status = "success"
                except Exception:
                    app.state.sync_status = "failed"
        finally:
            session.close()
        app.state.engine = engine
        app.state.session_factory = factory
        app.state.settings = settings
        if not settings.sync_on_start:
            app.state.sync_status = "not_run"
        yield
        engine.dispose()

    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.state.settings = settings
    application.state.sync_status = "not_run"
    register_error_handlers(application)
    install_request_guards(application)
    origins = settings.cors_origin_list()
    if settings.app_env != "production":
        origins = list(dict.fromkeys(origins + [
            "http://localhost:5500",
            "http://127.0.0.1:5500",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]))
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    _apply_security_headers(application)
    application.include_router(health.router, prefix="/api/v1")
    application.include_router(opportunities.router, prefix="/api/v1")
    application.include_router(health_topics.router, prefix="/api/v1")
    application.include_router(eligibility.router, prefix="/api/v1")
    application.include_router(plan.router, prefix="/api/v1")
    application.include_router(admin.router, prefix="/api/v1")
    application.include_router(chat.router, prefix="/api/v1")
    application.include_router(auth.router, prefix="/api/v1")
    application.include_router(citizen.router, prefix="/api/v1")
    Path("data").mkdir(exist_ok=True)
    ui_directory = Path(__file__).resolve().parent.parent / "ui"
    application.mount("/", StaticFiles(directory=ui_directory, html=True), name="ui")
    return application


app = create_app()
