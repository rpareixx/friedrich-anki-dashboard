from datetime import date

import pytest
from sqlalchemy.orm import Session

from dashboard.bonus_engine import apply_stats


def _apply(session: Session, target: date, reviews: int, threshold: int = 20):
    return apply_stats(
        session=session,
        user_slug="robert",
        brawler_subject="englisch",
        target_date=target,
        reviews_count=reviews,
        daily_goal_threshold=threshold,
    )


def test_below_threshold_no_achievement(session: Session) -> None:
    r = _apply(session, date(2026, 5, 8), reviews=10)
    assert r.achievement_unlocked is False
    assert r.daily_stat.achieved is False
    assert r.brawler.coins_total == 0
    assert r.brawler.streak_current == 0


def test_at_threshold_unlocks_achievement(session: Session) -> None:
    r = _apply(session, date(2026, 5, 8), reviews=20)
    assert r.achievement_unlocked is True
    assert r.daily_stat.achieved is True
    assert r.brawler.coins_total == 1
    assert r.brawler.streak_current == 1
    assert r.brawler.streak_max == 1


def test_above_threshold_unlocks_achievement(session: Session) -> None:
    r = _apply(session, date(2026, 5, 8), reviews=42)
    assert r.daily_stat.achieved is True
    assert r.brawler.coins_total == 1


def test_idempotent_same_day_same_count(session: Session) -> None:
    _apply(session, date(2026, 5, 8), reviews=25)
    r2 = _apply(session, date(2026, 5, 8), reviews=25)
    assert r2.achievement_unlocked is False
    assert r2.brawler.coins_total == 1
    assert r2.brawler.streak_current == 1


def test_idempotent_same_day_higher_count(session: Session) -> None:
    _apply(session, date(2026, 5, 8), reviews=25)
    r2 = _apply(session, date(2026, 5, 8), reviews=50)
    assert r2.achievement_unlocked is False
    assert r2.brawler.coins_total == 1
    assert r2.daily_stat.reviews_count == 50


def test_late_unlock_same_day(session: Session) -> None:
    _apply(session, date(2026, 5, 8), reviews=15)
    r2 = _apply(session, date(2026, 5, 8), reviews=25)
    assert r2.achievement_unlocked is True
    assert r2.brawler.coins_total == 1
    assert r2.brawler.streak_current == 1


def test_consecutive_days_chain_streak(session: Session) -> None:
    _apply(session, date(2026, 5, 7), reviews=20)
    r = _apply(session, date(2026, 5, 8), reviews=20)
    assert r.brawler.streak_current == 2
    assert r.brawler.streak_max == 2
    assert r.brawler.coins_total == 2


def test_three_consecutive_days(session: Session) -> None:
    _apply(session, date(2026, 5, 6), reviews=20)
    _apply(session, date(2026, 5, 7), reviews=20)
    r = _apply(session, date(2026, 5, 8), reviews=20)
    assert r.brawler.streak_current == 3
    assert r.brawler.streak_max == 3
    assert r.brawler.coins_total == 3


def test_day_gap_resets_streak(session: Session) -> None:
    _apply(session, date(2026, 5, 6), reviews=20)
    r = _apply(session, date(2026, 5, 8), reviews=20)
    assert r.brawler.streak_current == 1
    assert r.brawler.streak_max == 1
    assert r.brawler.coins_total == 2


def test_streak_max_persists_after_break(session: Session) -> None:
    _apply(session, date(2026, 5, 5), reviews=20)
    _apply(session, date(2026, 5, 6), reviews=20)
    _apply(session, date(2026, 5, 7), reviews=20)
    r = _apply(session, date(2026, 5, 9), reviews=20)
    assert r.brawler.streak_current == 1
    assert r.brawler.streak_max == 3


def test_unknown_user_raises(session: Session) -> None:
    with pytest.raises(ValueError, match="unknown user"):
        apply_stats(
            session=session,
            user_slug="unknown",
            brawler_subject="englisch",
            target_date=date(2026, 5, 8),
            reviews_count=20,
            daily_goal_threshold=20,
        )


def test_unknown_brawler_raises(session: Session) -> None:
    with pytest.raises(ValueError, match="unknown brawler"):
        apply_stats(
            session=session,
            user_slug="robert",
            brawler_subject="quantum-physics",
            target_date=date(2026, 5, 8),
            reviews_count=20,
            daily_goal_threshold=20,
        )


def test_low_count_after_high_count_keeps_achievement(session: Session) -> None:
    _apply(session, date(2026, 5, 8), reviews=30)
    r2 = _apply(session, date(2026, 5, 8), reviews=10)
    assert r2.daily_stat.achieved is True
    assert r2.daily_stat.reviews_count == 30
    assert r2.brawler.coins_total == 1
