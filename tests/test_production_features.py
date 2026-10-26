from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import Base, make_engine, make_session_factory
from app.models import SyncLog
from app.services.sync import sync_source


def test_sync_source_upserts_records_and_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "sync.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    get_settings.cache_clear()
    engine = make_engine()
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)
    payload = {
        "opportunities": [{
            "id": "sync-opportunity",
            "title": "Synced opportunity",
            "category": "job",
            "description": "A synced record",
            "criteria": {"needs": ["work"]},
            "documents": ["Application form"],
            "official_url": "https://example.gov/apply",
            "updated_at": "2026-01-01T00:00:00",
        }],
        "health_topics": [],
    }
    with respx.mock:
        route = respx.get("https://example.gov/catalogue.json").mock(return_value=httpx.Response(200, json=payload))
        with factory() as session:
            log = sync_source(session, "https://example.gov/catalogue.json")
            assert route.called
            assert log.status == "success"
            assert log.records_upserted == 1
            assert session.query(SyncLog).count() == 1
    engine.dispose()
    get_settings.cache_clear()


def test_admin_requires_key_and_can_upsert(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'admin.db').as_posix()}")
    monkeypatch.setenv("ADMIN_API_KEY", "test-secret")
    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as client:
        payload = {
            "id": "admin-job",
            "title": "Admin job",
            "category": "job",
            "description": "Managed by an admin",
            "criteria": {"needs": ["work"]},
        }
        assert client.put("/api/v1/admin/opportunities/admin-job", json=payload).status_code == 401
        response = client.put(
            "/api/v1/admin/opportunities/admin-job",
            json=payload,
            headers={"X-Admin-Api-Key": "test-secret"},
        )
        assert response.status_code == 200
        assert client.get("/api/v1/opportunities/admin-job").status_code == 200
    get_settings.cache_clear()


def test_ai_falls_back_to_template_without_provider_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    get_settings.cache_clear()
    from app.services.ai import explain

    class Session:
        def get(self, *_args):
            return None

    assert explain("prompt", "fallback", Session()) == ("fallback", "template")
    get_settings.cache_clear()
