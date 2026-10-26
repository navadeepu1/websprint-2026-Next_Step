from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, make_engine, make_session_factory
from app.errors import register_error_handlers
from app.routers import eligibility, health, health_topics, opportunities, plan
from app.seed import database_is_empty, load_seed_data


def _apply_security_headers(app: FastAPI) -> None:
    @app.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
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
            if database_is_empty(session):
                load_seed_data(session)
        finally:
            session.close()
        app.state.engine = engine
        app.state.session_factory = factory
        app.state.settings = settings
        app.state.sync_status = "not_run"
        yield
        engine.dispose()

    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.state.settings = settings
    application.state.sync_status = "not_run"
    register_error_handlers(application)
    origins = settings.cors_origin_list()
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
    Path("data").mkdir(exist_ok=True)
    return application


app = create_app()
