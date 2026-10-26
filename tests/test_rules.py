from app.eligibility.money import format_inr
from app.eligibility.rules import (
    rule_age,
    rule_disability,
    rule_education,
    rule_income,
    rule_land,
    rule_need,
    rule_occupation,
    rule_state,
)
from app.eligibility.types import Profile, RuleResult


def sample_profile(**overrides) -> Profile:
    data = {
        "age": 22,
        "education_level": "undergraduate",
        "occupation": "student",
        "annual_income": 120000,
        "state": "PB",
        "need": ["study"],
        "has_land": None,
        "has_disability": None,
    }
    data.update(overrides)
    return Profile(**data)


def test_format_inr() -> None:
    assert format_inr(250000) == "₹2,50,000"
    assert format_inr(1000) == "₹1,000"
    assert format_inr(99) == "₹99"


def test_age_pass_fail_unknown_skip_and_bounds() -> None:
    profile = sample_profile(age=18)
    assert rule_age(profile, {}) is None
    assert rule_age(profile, {"min_age": None, "max_age": None}) is None
    assert rule_age(profile, {"min_age": 18, "max_age": 18}).result == RuleResult.PASS
    assert rule_age(profile, {"min_age": 18}).result == RuleResult.PASS
    assert rule_age(sample_profile(age=17), {"min_age": 18}).result == RuleResult.FAIL
    assert rule_age(sample_profile(age=26), {"max_age": 25}).result == RuleResult.FAIL


def test_education_occupation_pass_fail_skip() -> None:
    profile = sample_profile()
    assert rule_education(profile, {}) is None
    assert rule_education(profile, {"education_levels": []}) is None
    assert rule_education(profile, {"education_levels": ["undergraduate"]}).result == RuleResult.PASS
    assert rule_education(profile, {"education_levels": ["12th"]}).result == RuleResult.FAIL
    assert rule_occupation(profile, {"occupations": ["student"]}).result == RuleResult.PASS
    assert rule_occupation(profile, {"occupations": ["farmer"]}).result == RuleResult.FAIL
    assert rule_occupation(profile, {"occupations": None}) is None


def test_income_inclusive_limit() -> None:
    profile = sample_profile(annual_income=250000)
    assert rule_income(profile, {}) is None
    assert rule_income(profile, {"max_annual_income": 250000}).result == RuleResult.PASS
    failed = rule_income(sample_profile(annual_income=250001), {"max_annual_income": 250000})
    assert failed.result == RuleResult.FAIL
    assert "₹2,50,000" in failed.near_miss


def test_state_all_listed_and_unspecified() -> None:
    assert rule_state(sample_profile(), {"states": ["ALL"]}).result == RuleResult.PASS
    assert rule_state(sample_profile(state="PB"), {"states": ["PB"]}).result == RuleResult.PASS
    assert rule_state(sample_profile(state="PB"), {"states": ["HR"]}).result == RuleResult.FAIL
    assert rule_state(sample_profile(state="ALL"), {"states": ["PB"]}).result == RuleResult.UNKNOWN
    assert rule_state(sample_profile(), {"states": []}) is None


def test_need_overlap() -> None:
    profile = sample_profile(need=["study", "work"])
    assert rule_need(profile, {"needs": ["work"]}).result == RuleResult.PASS
    assert rule_need(profile, {"needs": ["farming"]}).result == RuleResult.FAIL
    assert rule_need(profile, {"needs": []}) is None


def test_land_and_disability_unknown_only_when_unanswered() -> None:
    unanswered = sample_profile(has_land=None, has_disability=None)
    assert rule_land(unanswered, {"requires_land": True}).result == RuleResult.UNKNOWN
    assert rule_disability(unanswered, {"disability_required": True}).result == RuleResult.UNKNOWN
    assert rule_land(sample_profile(has_land=True), {"requires_land": True}).result == RuleResult.PASS
    assert rule_land(sample_profile(has_land=False), {"requires_land": True}).result == RuleResult.FAIL
    assert rule_land(sample_profile(has_land=False), {"requires_land": False}).result == RuleResult.PASS
    assert rule_disability(sample_profile(has_disability=True), {"disability_required": True}).result == RuleResult.PASS
    assert rule_disability(sample_profile(has_disability=False), {"disability_required": True}).result == RuleResult.FAIL
    assert rule_land(unanswered, {"requires_land": None}) is None
    assert rule_disability(unanswered, {}) is None
