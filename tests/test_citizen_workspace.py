from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings


def test_authenticated_citizen_can_save_profile_opportunity_and_application(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'workspace.db').as_posix()}")
    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as client:
        login = client.post("/api/v1/auth/login", json={"email": "demo@nextstep.local", "password": "Demo@12345"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        profile = {
            "age": 22,
            "education_level": "undergraduate",
            "occupation": "student",
            "annual_income": 0,
            "state": "PB",
            "need": ["study"],
        }

        assert client.put("/api/v1/profile", json=profile, headers=headers).status_code == 200
        assert client.get("/api/v1/profile", headers=headers).json()["occupation"] == "student"

        opportunities = client.get("/api/v1/opportunities?active=true", headers=headers).json()
        opportunity_id = opportunities[0]["id"]
        assert client.post(f"/api/v1/saved-opportunities/{opportunity_id}", headers=headers).status_code == 201
        assert client.get("/api/v1/saved-opportunities", headers=headers).json()[0]["opportunity"]["id"] == opportunity_id

        created = client.post(
            "/api/v1/applications",
            json={"opportunity_id": opportunity_id, "status": "preparing", "next_step": "Collect documents"},
            headers=headers,
        )
        assert created.status_code == 201
        tracker_id = created.json()["id"]
        updated = client.patch(f"/api/v1/applications/{tracker_id}", json={"status": "submitted"}, headers=headers)
        assert updated.status_code == 200
        assert updated.json()["status"] == "submitted"
    get_settings.cache_clear()
