from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dashboard.models import Brawler, DailyStat, User


def test_robert_seed_exists(session: Session) -> None:
    robert = session.execute(select(User).where(User.slug == "robert")).scalar_one()
    assert robert.email == "robert.parei@parei.eu"
    assert robert.timezone == "Europe/Berlin"


def test_robert_has_englisch_brawler_in_slot_1(session: Session) -> None:
    robert = session.execute(select(User).where(User.slug == "robert")).scalar_one()
    assert len(robert.brawlers) == 1
    brawler = robert.brawlers[0]
    assert brawler.subject == "englisch"
    assert brawler.slot == 1
    assert brawler.coins_total == 0
    assert brawler.streak_current == 0
    assert brawler.streak_max == 0


def test_users_slug_is_unique(session: Session) -> None:
    session.add(User(slug="robert", email="dupe@example.com"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_brawlers_user_slot_is_unique(session: Session) -> None:
    robert = session.execute(select(User).where(User.slug == "robert")).scalar_one()
    session.add(Brawler(user_id=robert.id, slot=1, subject="mathe"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_brawler_can_have_multiple_slots(session: Session) -> None:
    robert = session.execute(select(User).where(User.slug == "robert")).scalar_one()
    session.add(Brawler(user_id=robert.id, slot=2, subject="mathe"))
    session.commit()

    refreshed = session.execute(select(User).where(User.slug == "robert")).scalar_one()
    assert len(refreshed.brawlers) == 2
    subjects = {b.subject for b in refreshed.brawlers}
    assert subjects == {"englisch", "mathe"}


def test_daily_stats_brawler_date_is_unique(session: Session) -> None:
    robert = session.execute(select(User).where(User.slug == "robert")).scalar_one()
    brawler = robert.brawlers[0]
    session.add(DailyStat(brawler_id=brawler.id, date=date(2026, 5, 8), reviews_count=20))
    session.commit()

    session.add(DailyStat(brawler_id=brawler.id, date=date(2026, 5, 8), reviews_count=30))
    with pytest.raises(IntegrityError):
        session.commit()


def test_cascade_delete_user_removes_brawlers_and_stats(session: Session) -> None:
    robert = session.execute(select(User).where(User.slug == "robert")).scalar_one()
    brawler = robert.brawlers[0]
    session.add(DailyStat(brawler_id=brawler.id, date=date(2026, 5, 8), reviews_count=20))
    session.commit()

    session.delete(robert)
    session.commit()

    assert session.execute(select(User)).first() is None
    assert session.execute(select(Brawler)).first() is None
    assert session.execute(select(DailyStat)).first() is None
