from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.constants import HEALTH_DISCLAIMER


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'db.sqlite').as_posix()}")
    monkeypatch.setenv("SYNC_ON_START", "false")
    monkeypatch.setenv("AI_PROVIDER", "noop")
    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


def profile_payload(**overrides) -> dict:
    data = {
        "age": 20,
        "education_level": "undergraduate",
        "occupation": "student",
        "annual_income": 50000,
        "state": "PB",
        "need": ["study"],
    }
    data.update(overrides)
    return data


def test_eligibility_check_sorted_and_counts(client: TestClient) -> None:
    response = client.post("/api/v1/eligibility/check", json=profile_payload())
    assert response.status_code == 200
    body = response.json()
    statuses = [item["status"] for item in body["results"]]
    order = {"ELIGIBLE": 0, "POSSIBLY_ELIGIBLE": 1, "NOT_ELIGIBLE": 2}
    assert statuses == sorted(statuses, key=lambda item: order[item])
    assert sum(body["counts"].values()) == len(body["results"])
    assert body["explanation_source"] == "template"
    assert body["health_topics"] == []


def test_eligibility_includes_health_topics_when_needed(client: TestClient) -> None:
    response = client.post("/api/v1/eligibility/check", json=profile_payload(need=["study", "health"]))
    assert response.status_code == 200
    body = response.json()
    assert body["health_disclaimer"] == HEALTH_DISCLAIMER
    assert body["health_topics"]


def test_plan_json_and_markdown(client: TestClient) -> None:
    json_response = client.post("/api/v1/plan", json=profile_payload())
    assert json_response.status_code == 200
    assert "checklist" in json_response.json()
    markdown = client.post("/api/v1/plan?format=markdown", json=profile_payload())
    assert markdown.status_code == 200
    assert markdown.headers["content-type"].startswith("text/markdown")
    assert markdown.text.startswith("# NextStep action plan")


def test_invalid_age_message(client: TestClient) -> None:
    response = client.post("/api/v1/eligibility/check", json=profile_payload(age=200))
    assert response.status_code == 422
    assert response.json()["error"]["message"] == "Age must be between 0 and 120."
