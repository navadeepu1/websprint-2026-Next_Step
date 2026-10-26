from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.eligibility.money import format_inr
from app.eligibility.types import Profile, RuleOutcome, RuleResult

RuleFn = Callable[[Profile, dict[str, Any]], RuleOutcome | None]


def _is_empty(value: Any) -> bool:
    return value is None or value == [] or value == ""


def rule_age(profile: Profile, criteria: dict[str, Any]) -> RuleOutcome | None:
    min_age = criteria.get("min_age")
    max_age = criteria.get("max_age")
    if _is_empty(min_age) and _is_empty(max_age):
        return None
    low = 0 if _is_empty(min_age) else int(min_age)
    high = 120 if _is_empty(max_age) else int(max_age)
    if low <= profile.age <= high:
        return RuleOutcome("age", RuleResult.PASS, f"Age {profile.age} is within the allowed range.")
    if profile.age < low:
        return RuleOutcome(
            "age",
            RuleResult.FAIL,
            f"Age {profile.age} is below the minimum age of {low}.",
            near_miss=f"This scheme requires age {low} or above. Your age is below this limit.",
        )
    return RuleOutcome(
        "age",
        RuleResult.FAIL,
        f"Age {profile.age} is above the maximum age of {high}.",
        near_miss=f"This scheme requires age {high} or below. Your age is above this limit.",
    )


def rule_education(profile: Profile, criteria: dict[str, Any]) -> RuleOutcome | None:
    levels = criteria.get("education_levels")
    if _is_empty(levels):
        return None
    if profile.education_level in levels:
        return RuleOutcome("education", RuleResult.PASS, "Education level matches the scheme list.")
    return RuleOutcome(
        "education",
        RuleResult.FAIL,
        "Education level is not in the scheme list.",
        near_miss="This scheme requires a listed education level that does not match your profile.",
    )


def rule_occupation(profile: Profile, criteria: dict[str, Any]) -> RuleOutcome | None:
    occupations = criteria.get("occupations")
    if _is_empty(occupations):
        return None
    if profile.occupation in occupations:
        return RuleOutcome("occupation", RuleResult.PASS, "Occupation matches the scheme list.")
    return RuleOutcome(
        "occupation",
        RuleResult.FAIL,
        "Occupation is not in the scheme list.",
        near_miss="This scheme is limited to listed occupations that do not match your profile.",
    )


def rule_income(profile: Profile, criteria: dict[str, Any]) -> RuleOutcome | None:
    limit = criteria.get("max_annual_income")
    if _is_empty(limit):
        return None
    limit_int = int(limit)
    if profile.annual_income <= limit_int:
        return RuleOutcome(
            "income",
            RuleResult.PASS,
            f"Annual income is at or below {format_inr(limit_int)}.",
        )
    return RuleOutcome(
        "income",
        RuleResult.FAIL,
        f"Annual income is above {format_inr(limit_int)}.",
        near_miss=(
            f"This scheme requires annual income of {format_inr(limit_int)} or less. "
            "Your income is above this limit."
        ),
    )


def rule_state(profile: Profile, criteria: dict[str, Any]) -> RuleOutcome | None:
    states = criteria.get("states")
    if _is_empty(states):
        return None
    normalized = [str(item).upper() for item in states]
    if "ALL" in normalized:
        return RuleOutcome("state", RuleResult.PASS, "This scheme is open in all listed states.")
    if profile.state == "ALL":
        return RuleOutcome(
            "state",
            RuleResult.UNKNOWN,
            "Your state was not specified, so state eligibility cannot be confirmed.",
        )
    if profile.state in normalized:
        return RuleOutcome("state", RuleResult.PASS, f"State {profile.state} is listed.")
    return RuleOutcome(
        "state",
        RuleResult.FAIL,
        f"State {profile.state} is not listed.",
        near_miss="This scheme is limited to other states. Your state is not on the list.",
    )


def rule_need(profile: Profile, criteria: dict[str, Any]) -> RuleOutcome | None:
    needs = criteria.get("needs")
    if _is_empty(needs):
        return None
    if set(profile.need) & set(needs):
        return RuleOutcome("need", RuleResult.PASS, "At least one stated need overlaps the scheme.")
    return RuleOutcome(
        "need",
        RuleResult.FAIL,
        "None of the stated needs overlap this scheme.",
        near_miss="This scheme targets a different need than the ones you selected.",
    )


def rule_land(profile: Profile, criteria: dict[str, Any]) -> RuleOutcome | None:
    required = criteria.get("requires_land")
    if required is None:
        return None
    if profile.has_land is None:
        return RuleOutcome(
            "land",
            RuleResult.UNKNOWN,
            "Land ownership was not answered, so this rule cannot be confirmed.",
        )
    if bool(required) == profile.has_land:
        return RuleOutcome("land", RuleResult.PASS, "Land answer matches the scheme requirement.")
    if required:
        miss = "This scheme requires land. Your profile says you do not have land."
    else:
        miss = "This scheme is for people without land. Your profile says you have land."
    return RuleOutcome("land", RuleResult.FAIL, "Land answer does not match the scheme requirement.", near_miss=miss)


def rule_disability(profile: Profile, criteria: dict[str, Any]) -> RuleOutcome | None:
    required = criteria.get("disability_required")
    if required is None:
        return None
    if profile.has_disability is None:
        return RuleOutcome(
            "disability",
            RuleResult.UNKNOWN,
            "Disability was not answered, so this rule cannot be confirmed.",
        )
    if bool(required) == profile.has_disability:
        return RuleOutcome("disability", RuleResult.PASS, "Disability answer matches the scheme requirement.")
    if required:
        miss = "This scheme requires a notified disability. Your profile says you do not have one."
    else:
        miss = "This scheme is not limited to disability. Your profile does not match this requirement."
    return RuleOutcome(
        "disability",
        RuleResult.FAIL,
        "Disability answer does not match the scheme requirement.",
        near_miss=miss,
    )


RULE_REGISTRY: dict[str, RuleFn] = {
    "age": rule_age,
    "education": rule_education,
    "occupation": rule_occupation,
    "income": rule_income,
    "state": rule_state,
    "need": rule_need,
    "land": rule_land,
    "disability": rule_disability,
}
