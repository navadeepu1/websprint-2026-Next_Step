from app.eligibility.engine import evaluate_all, evaluate_opportunity
from app.eligibility.types import EligibilityStatus, Profile


def profile(**overrides) -> Profile:
    data = {
        "age": 21,
        "education_level": "undergraduate",
        "occupation": "student",
        "annual_income": 80000,
        "state": "PB",
        "need": ["study"],
        "has_land": None,
        "has_disability": None,
    }
    data.update(overrides)
    return Profile(**data)


def opportunity(**overrides) -> dict:
    data = {
        "id": "sample-scheme",
        "title": "Sample Scheme",
        "category": "scholarship",
        "criteria": {
            "min_age": 18,
            "max_age": 25,
            "education_levels": ["undergraduate"],
            "occupations": ["student"],
            "max_annual_income": 250000,
            "states": ["ALL"],
            "needs": ["study"],
            "requires_land": None,
            "disability_required": None,
        },
        "documents": ["Income certificate"],
        "official_url": "https://scholarships.gov.in/",
        "source_name": "NSP",
        "last_verified": None,
        "verified": False,
    }
    data.update(overrides)
    return data


def test_all_pass_is_eligible() -> None:
    result = evaluate_opportunity(profile(), opportunity())
    assert result.status == EligibilityStatus.ELIGIBLE
    assert result.near_miss is None


def test_unknown_without_fail_is_possibly_eligible() -> None:
    result = evaluate_opportunity(
        profile(),
        opportunity(criteria={"requires_land": True, "states": ["ALL"], "needs": ["study"]}),
    )
    assert result.status == EligibilityStatus.POSSIBLY_ELIGIBLE


def test_any_fail_is_not_eligible_with_near_miss() -> None:
    result = evaluate_opportunity(
        profile(annual_income=300000),
        opportunity(),
    )
    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert "₹2,50,000" in (result.near_miss or "")


def test_empty_criteria_skips_rules_and_is_eligible() -> None:
    result = evaluate_opportunity(profile(), opportunity(criteria={}))
    assert result.status == EligibilityStatus.ELIGIBLE
    assert result.reasons == []


def test_sort_by_status_then_title() -> None:
    items = [
        opportunity(id="b-no", title="Beta Closed", criteria={"min_age": 60}),
        opportunity(id="a-yes", title="Alpha Open", criteria={"states": ["ALL"]}),
        opportunity(id="c-maybe", title="Gamma Maybe", criteria={"requires_land": True}),
    ]
    results = evaluate_all(profile(), items)
    assert [item.id for item in results] == ["a-yes", "c-maybe", "b-no"]
