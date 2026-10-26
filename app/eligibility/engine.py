from __future__ import annotations

from typing import Any

from app.eligibility.rules import RULE_REGISTRY
from app.eligibility.types import EligibilityResult, EligibilityStatus, Profile, RuleResult

STATUS_ORDER = {
    EligibilityStatus.ELIGIBLE: 0,
    EligibilityStatus.POSSIBLY_ELIGIBLE: 1,
    EligibilityStatus.NOT_ELIGIBLE: 2,
}


def evaluate_opportunity(profile: Profile, opportunity: dict[str, Any]) -> EligibilityResult:
    criteria = opportunity.get("criteria") or {}
    reasons = []
    for _name, fn in RULE_REGISTRY.items():
        outcome = fn(profile, criteria)
        if outcome is not None:
            reasons.append(outcome)
    results = [item.result for item in reasons]
    if any(item == RuleResult.FAIL for item in results):
        status = EligibilityStatus.NOT_ELIGIBLE
        near_miss = next((item.near_miss for item in reasons if item.result == RuleResult.FAIL and item.near_miss), None)
    elif any(item == RuleResult.UNKNOWN for item in results):
        status = EligibilityStatus.POSSIBLY_ELIGIBLE
        near_miss = None
    else:
        status = EligibilityStatus.ELIGIBLE
        near_miss = None
    last_verified = opportunity.get("last_verified")
    if last_verified is not None:
        last_verified = str(last_verified)
    return EligibilityResult(
        id=opportunity["id"],
        title=opportunity["title"],
        category=opportunity["category"],
        status=status,
        reasons=reasons,
        near_miss=near_miss,
        documents=list(opportunity.get("documents") or []),
        official_url=opportunity.get("official_url"),
        source_name=opportunity.get("source_name"),
        last_verified=last_verified,
        verified=bool(opportunity.get("verified", False)),
        criteria=criteria,
    )


def evaluate_all(profile: Profile, opportunities: list[dict[str, Any]]) -> list[EligibilityResult]:
    results = [evaluate_opportunity(profile, item) for item in opportunities]
    return sorted(results, key=lambda item: (STATUS_ORDER[item.status], item.title.lower()))
