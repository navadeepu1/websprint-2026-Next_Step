from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, make_engine, make_session_factory
from app.seed import load_seed_data


@pytest.fixture
def db_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Session:
    db_path = tmp_path / "nextstep.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    get_settings.cache_clear()
    engine = make_engine(f"sqlite:///{db_path.as_posix()}")
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        get_settings.cache_clear()


@pytest.fixture
def seeded_session(db_session: Session) -> Session:
    load_seed_data(db_session)
    return db_session
