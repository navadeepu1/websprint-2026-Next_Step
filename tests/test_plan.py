from app.eligibility.types import EligibilityResult, EligibilityStatus, Profile, RuleOutcome, RuleResult
from app.services.plan import build_plan, plan_to_markdown


def _result(status: EligibilityStatus, **overrides) -> EligibilityResult:
    data = {
        "id": "scheme-a",
        "title": "Scheme A",
        "category": "scholarship",
        "status": status,
        "reasons": [],
        "near_miss": None,
        "documents": ["Income certificate", "School ID"],
        "official_url": "https://scholarships.gov.in/",
        "source_name": "NSP",
        "last_verified": None,
        "verified": False,
        "criteria": {},
    }
    data.update(overrides)
    return EligibilityResult(**data)


def test_plan_deduplicates_documents_and_orders_steps() -> None:
    profile = Profile(21, "undergraduate", "student", 1, "PB", ["study"], None, None)
    first = _result(EligibilityStatus.ELIGIBLE)
    second = _result(
        EligibilityStatus.POSSIBLY_ELIGIBLE,
        id="scheme-b",
        title="Scheme B",
        documents=["Income certificate", "Caste certificate"],
        reasons=[RuleOutcome("land", RuleResult.UNKNOWN, "missing")],
        official_url="https://www.myscheme.gov.in/",
    )
    skipped = _result(EligibilityStatus.NOT_ELIGIBLE, id="scheme-c", title="Scheme C", documents=["Should skip"])
    plan = build_plan(profile, [first, second, skipped], "template text", "template")
    assert plan.documents == ["Income certificate", "School ID", "Caste certificate"]
    texts = [item.text for item in plan.checklist]
    assert texts[0].startswith("Answer whether you own agricultural land.")
    assert any("Gather this document: Income certificate" in text for text in texts)
    assert any("Visit the official page" in text for text in texts)
    assert all("Should skip" not in text for text in texts)
    assert plan.warnings
    markdown = plan_to_markdown(plan)
    assert markdown.startswith("# NextStep action plan")
    assert "Income certificate" in markdown
