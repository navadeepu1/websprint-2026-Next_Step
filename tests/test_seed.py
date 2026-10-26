from sqlalchemy import func, select

from app.models import HealthTopic, Opportunity
from app.seed import database_is_empty, load_seed_data


def test_database_starts_empty(db_session) -> None:
    assert database_is_empty(db_session) is True


def test_seed_loads_minimum_records(seeded_session) -> None:
    opportunities = list(seeded_session.scalars(select(Opportunity)))
    topics = list(seeded_session.scalars(select(HealthTopic)))
    assert len(opportunities) >= 15
    assert len(topics) >= 8
    by_category: dict[str, int] = {}
    for item in opportunities:
        by_category[item.category] = by_category.get(item.category, 0) + 1
        assert item.verified is False
    assert by_category.get("scholarship", 0) >= 5
    assert by_category.get("job", 0) >= 5
    assert by_category.get("farmer_scheme", 0) >= 5
    assert by_category.get("senior_support", 0) >= 5


def test_seed_is_idempotent_via_merge(seeded_session) -> None:
    first = seeded_session.scalar(select(func.count()).select_from(Opportunity))
    load_seed_data(seeded_session)
    second = seeded_session.scalar(select(func.count()).select_from(Opportunity))
    assert first == second
