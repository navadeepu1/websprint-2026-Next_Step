import os

import pytest

playwright = pytest.importorskip("playwright.sync_api")


@pytest.mark.e2e
def test_ui_core_navigation_and_profile_submission() -> None:
    """Run with a local server and `pytest -m e2e tests/e2e` after installing Playwright."""
    with playwright.sync_playwright() as api:
        browser = api.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(os.getenv("NEXTSTEP_BASE_URL", "http://127.0.0.1:8000/"))
        assert page.get_by_role("heading", name="Find support that fits your next step.").is_visible()
        page.get_by_role("link", name="Check eligibility").click()
        page.get_by_role("button", name="Check opportunities").click()
        assert page.locator("#eligibility-results").is_visible()
        browser.close()
