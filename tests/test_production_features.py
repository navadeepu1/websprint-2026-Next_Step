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


def test_groq_explanation_uses_bearer_auth_and_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'groq.db').as_posix()}")
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("GROQ_MODEL", "test-model")
    get_settings.cache_clear()
    engine = make_engine()
    Base.metadata.create_all(engine)
    factory = make_session_factory(engine)

    with respx.mock:
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "A clearer explanation."}}]},
            )
        )
        from app.services.ai import explain

        with factory() as session:
            assert explain("prompt", "fallback", session) == ("A clearer explanation.", "ai")
            assert explain("prompt", "fallback", session) == ("A clearer explanation.", "ai")
        assert route.call_count == 1
        assert route.calls[0].request.headers["Authorization"] == "Bearer test-groq-key"
        request = route.calls[0].request
        assert request.content and b'"model":"test-model"' in request.content

    engine.dispose()
    get_settings.cache_clear()


def test_chatbot_template_guidance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "noop")
    get_settings.cache_clear()
    from app.services.chat import answer_chat

    reply, source = answer_chat("Where do I check eligibility?", [])
    assert source == "template"
    assert "Check eligibility" in reply
    get_settings.cache_clear()


def test_chatbot_uses_groq_with_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'chat.db').as_posix()}")
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-chat-key")
    get_settings.cache_clear()
    from app.services.chat import answer_chat

    with respx.mock:
        route = respx.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Open Opportunities to browse records."}}]},
            )
        )
        reply, source = answer_chat("Where can I browse schemes?", [{"role": "user", "content": "Hi"}])
        assert source == "ai"
        assert "Opportunities" in reply
        assert route.calls[0].request.headers["Authorization"] == "Bearer test-chat-key"
        assert b"Where can I browse schemes?" in route.calls[0].request.content
    get_settings.cache_clear()


def test_chat_endpoint_returns_structured_response(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'chat-api.db').as_posix()}")
    monkeypatch.setenv("AI_PROVIDER", "noop")
    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/chat",
            json={"message": "Where are the API docs?", "history": []},
        )
    assert response.status_code == 200
    assert response.json()["source"] == "template"
    assert response.json()["provider"] == "template"
    assert "/docs" in response.json()["reply"]
    get_settings.cache_clear()
