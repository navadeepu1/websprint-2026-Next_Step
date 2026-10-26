from app.eligibility.types import EligibilityResult, Profile


def template_explanation(profile: Profile, results: list[EligibilityResult]) -> str:
    if not results:
        return (
            "No active schemes were available to compare with this profile. "
            "NextStep did not invent any programmes."
        )
    eligible = [item.title for item in results if item.status.value == "ELIGIBLE"]
    possible = [item.title for item in results if item.status.value == "POSSIBLY_ELIGIBLE"]
    rejected = [item.title for item in results if item.status.value == "NOT_ELIGIBLE"]
    parts = [
        "This summary is produced from the eligibility rules, not from a model guess.",
        f"The profile used age {profile.age}, occupation {profile.occupation}, and needs {', '.join(profile.need)}.",
    ]
    if eligible:
        parts.append("Likely matches: " + "; ".join(eligible) + ".")
    else:
        parts.append("No scheme was a full match on every confirmed rule.")
    if possible:
        parts.append(
            "Needs a missing answer before a firm yes or no: " + "; ".join(possible) + "."
        )
    if rejected:
        parts.append("Does not match at least one confirmed rule: " + "; ".join(rejected) + ".")
    parts.append("Confirm every detail on the official portal before you apply.")
    return " ".join(parts)
