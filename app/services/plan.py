from app.constants import UNVERIFIED_WARNING
from app.eligibility.types import EligibilityResult, EligibilityStatus, Profile, RuleResult
from app.schemas.plan import ChecklistItem, PlanOut

ACTIONABLE = {EligibilityStatus.ELIGIBLE, EligibilityStatus.POSSIBLY_ELIGIBLE}

QUESTION_TEXT = {
    "land": "Answer whether you own agricultural land.",
    "disability": "Answer whether you have a notified disability.",
    "state": "Specify the state where you live.",
}


def actionable_results(results: list[EligibilityResult]) -> list[EligibilityResult]:
    return [item for item in results if item.status in ACTIONABLE]


def build_plan(profile: Profile, results: list[EligibilityResult], explanation: str, explanation_source: str) -> PlanOut:
    selected = actionable_results(results)
    checklist: list[ChecklistItem] = []
    documents: list[str] = []
    links: list[dict[str, str | None]] = []
    warnings: list[str] = []
    seen_docs: set[str] = set()
    seen_links: set[str] = set()
    order = 1
    seen_questions: set[str] = set()
    for item in selected:
        for reason in item.reasons:
            if reason.result != RuleResult.UNKNOWN:
                continue
            text = QUESTION_TEXT.get(reason.rule, f"Provide the missing answer for {reason.rule}.")
            key = f"{reason.rule}:{text}"
            if key in seen_questions:
                continue
            seen_questions.add(key)
            checklist.append(ChecklistItem(order=order, text=f"{text} ({item.title})", opportunity_id=item.id))
            order += 1
        if not item.verified:
            warnings.append(f"{item.title}: {UNVERIFIED_WARNING}")
    for item in selected:
        for document in item.documents:
            if document not in seen_docs:
                seen_docs.add(document)
                documents.append(document)
                checklist.append(
                    ChecklistItem(
                        order=order,
                        text=f"Gather this document: {document} ({item.title})",
                        opportunity_id=item.id,
                    )
                )
                order += 1
        if item.official_url and item.official_url not in seen_links:
            seen_links.add(item.official_url)
            links.append({"title": item.title, "url": item.official_url})
            checklist.append(
                ChecklistItem(
                    order=order,
                    text=f"Visit the official page for {item.title}: {item.official_url}",
                    opportunity_id=item.id,
                )
            )
            order += 1
    if not checklist:
        checklist.append(
            ChecklistItem(
                order=1,
                text="No eligible or possibly eligible schemes were found. Review official portals if your situation changes.",
                opportunity_id=None,
            )
        )
    return PlanOut(
        checklist=checklist,
        documents=documents,
        links=links,
        warnings=warnings,
        explanation=explanation,
        explanation_source=explanation_source,
    )


def plan_to_markdown(plan: PlanOut) -> str:
    lines = ["# NextStep action plan", ""]
    lines.append("## Checklist")
    for item in plan.checklist:
        lines.append(f"{item.order}. {item.text}")
    lines.extend(["", "## Documents"])
    if plan.documents:
        for document in plan.documents:
            lines.append(f"- {document}")
    else:
        lines.append("- No document list is stored for these records yet. Confirm documents on the official portal.")
    lines.extend(["", "## Official links"])
    if plan.links:
        for link in plan.links:
            lines.append(f"- {link['title']}: {link['url']}")
    else:
        lines.append("- No official link is stored yet.")
    lines.extend(["", "## Warnings"])
    if plan.warnings:
        for warning in plan.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Explanation", plan.explanation, ""])
    return "\n".join(lines)
