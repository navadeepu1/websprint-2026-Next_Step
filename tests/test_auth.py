from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings


def test_demo_user_can_login_and_logout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'auth.db').as_posix()}")
    monkeypatch.setenv("AUTH_SECRET", "test-secret")
    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as client:
        login = client.post("/api/v1/auth/login", json={"email": "demo@nextstep.local", "password": "Demo@12345"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["display_name"] == "Demo Citizen"
        assert client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}).status_code == 200
        assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
    get_settings.cache_clear()


def test_user_can_register_and_duplicate_is_rejected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'register.db').as_posix()}")
    get_settings.cache_clear()
    from app.main import create_app

    with TestClient(create_app()) as client:
        payload = {"email": "new@example.com", "display_name": "New User", "password": "Password@123"}
        assert client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert client.post("/api/v1/auth/register", json=payload).status_code == 409
        assert client.post("/api/v1/auth/login", json={"email": payload["email"], "password": "wrong"}).status_code == 401
    get_settings.cache_clear()
