from fastapi.testclient import TestClient

from app.main import app


def test_ui_shell_and_assets_are_served() -> None:
    client = TestClient(app)

    page = client.get("/")
    stylesheet = client.get("/styles.css")
    script = client.get("/app.js")

    assert page.status_code == 200
    assert "NextStep" in page.text
    assert 'id="profile-form"' in page.text
    assert stylesheet.status_code == 200
    assert "--teal" in stylesheet.text
    assert script.status_code == 200
    assert "checkEligibility" in script.text
    assert "function initChatbot()" in script.text
    assert "initChatbot();" in script.text
    assert 'id="topic-search-form"' in page.text
    assert 'id="chat-launcher"' in page.text
