import pytest
from pydantic import ValidationError

from app.config import get_settings
from app.errors import FIELD_MESSAGES, _detail_from_error
from app.schemas.common import error_payload
from app.schemas.opportunity import OpportunityIn
from app.schemas.profile import ProfileIn


def _profile(**overrides):
    data = {
        "age": 20,
        "education_level": "undergraduate",
        "occupation": "student",
        "annual_income": 100000,
        "state": "PB",
        "need": ["study"],
    }
    data.update(overrides)
    return data


def test_profile_accepts_valid_payload() -> None:
    profile = ProfileIn(**_profile(has_land=None, has_disability=False))
    assert profile.state == "PB"
    assert profile.has_disability is False


def test_age_out_of_range() -> None:
    with pytest.raises(ValidationError) as exc:
        ProfileIn(**_profile(age=121))
    assert "Age must be between 0 and 120." in str(exc.value)


def test_age_zero_is_allowed() -> None:
    profile = ProfileIn(**_profile(age=0, education_level="none", occupation="other"))
    assert profile.age == 0


def test_income_upper_bound() -> None:
    with pytest.raises(ValidationError) as exc:
        ProfileIn(**_profile(annual_income=100_000_001))
    assert "Annual income must be between 0 and 100,000,000." in str(exc.value)


def test_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        ProfileIn(**_profile(aadhaar="1234"))


def test_need_must_be_unique() -> None:
    with pytest.raises(ValidationError):
        ProfileIn(**_profile(need=["study", "study"]))


def test_state_must_be_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOWED_STATES", "PB,ALL")
    get_settings.cache_clear()
    with pytest.raises(ValidationError) as exc:
        ProfileIn(**_profile(state="HR"))
    assert "State must be one of" in str(exc.value)
    get_settings.cache_clear()


def test_error_envelope_shape() -> None:
    payload = error_payload("validation_error", "Age must be between 0 and 120.", [{"field": "age", "message": FIELD_MESSAGES["age"]}])
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["details"][0]["field"] == "age"


def test_opportunity_rejects_unknown_category() -> None:
    with pytest.raises(ValidationError):
        OpportunityIn(
            id="bad-item",
            title="Bad",
            category="grant",
            description="x" * 10,
            criteria={},
        )


def test_detail_from_pydantic_value_error() -> None:
    detail = _detail_from_error({"loc": ["body", "age"], "msg": "Value error, Age must be between 0 and 120.", "type": "value_error"})
    assert detail["message"] == "Age must be between 0 and 120."
