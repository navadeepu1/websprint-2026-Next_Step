from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.constants import HEALTH_DISCLAIMER


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "nextstep.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("SYNC_ON_START", "false")
    monkeypatch.setenv("AI_PROVIDER", "noop")
    monkeypatch.setenv("CORS_ORIGINS", "")
    monkeypatch.setenv("ADMIN_API_KEY", "")
    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "ok"
    assert body["ai_provider"] == "noop"
    assert body["sync"] == "not_run"
    assert "X-Content-Type-Options" in response.headers


def test_opportunities_list_and_etag(client: TestClient) -> None:
    response = client.get("/api/v1/opportunities?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5
    assert response.headers["Cache-Control"] == "max-age=300"
    etag = response.headers["ETag"]
    again = client.get("/api/v1/opportunities?limit=5", headers={"If-None-Match": etag})
    assert again.status_code == 304


def test_opportunities_filters(client: TestClient) -> None:
    response = client.get("/api/v1/opportunities?category=scholarship&verified=false&active=true&limit=100")
    assert response.status_code == 200
    assert all(item["category"] == "scholarship" for item in response.json())


def test_opportunity_not_found_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/opportunities/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_opportunity_detail(client: TestClient) -> None:
    listing = client.get("/api/v1/opportunities?limit=1")
    item_id = listing.json()[0]["id"]
    response = client.get(f"/api/v1/opportunities/{item_id}")
    assert response.status_code == 200
    assert response.json()["id"] == item_id


def test_health_topics_include_disclaimer(client: TestClient) -> None:
    response = client.get("/api/v1/health-topics")
    assert response.status_code == 200
    assert len(response.json()) >= 8
    assert all(item["disclaimer"] == HEALTH_DISCLAIMER for item in response.json())


def test_health_topic_search_and_detail(client: TestClient) -> None:
    search = client.get("/api/v1/health-topics/search?q=heat")
    assert search.status_code == 200
    assert search.json()
    topic_id = search.json()[0]["id"]
    detail = client.get(f"/api/v1/health-topics/{topic_id}")
    assert detail.status_code == 200
    assert detail.json()["disclaimer"] == HEALTH_DISCLAIMER
    missing = client.get("/api/v1/health-topics/missing-topic")
    assert missing.status_code == 404
    short = client.get("/api/v1/health-topics/search?q=a")
    assert short.status_code == 422
