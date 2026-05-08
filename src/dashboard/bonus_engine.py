from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from dashboard.models import Brawler, DailyStat, User


@dataclass
class StatsApplyResult:
    daily_stat: DailyStat
    brawler: Brawler
    achievement_unlocked: bool


def apply_stats(
    session: Session,
    user_slug: str,
    brawler_subject: str,
    target_date: date,
    reviews_count: int,
    daily_goal_threshold: int,
) -> StatsApplyResult:
    """Apply a stats push to the DB. Idempotent: re-applying with same or
    higher reviews_count never re-awards coins. Achievement is one-way
    (False -> True), never downgraded.

    Streak rules:
    - On achievement-unlock today: if yesterday was achieved, streak += 1; else streak = 1.
    - streak_max is updated.
    - Non-achievement today does NOT touch streak (streak only resets on
      next day's calculation).
    """
    user = session.execute(select(User).where(User.slug == user_slug)).scalar_one_or_none()
    if user is None:
        raise ValueError(f"unknown user: {user_slug}")

    brawler = session.execute(
        select(Brawler).where(
            Brawler.user_id == user.id, Brawler.subject == brawler_subject
        )
    ).scalar_one_or_none()
    if brawler is None:
        raise ValueError(f"unknown brawler: {user_slug}/{brawler_subject}")

    ds = session.execute(
        select(DailyStat).where(
            DailyStat.brawler_id == brawler.id, DailyStat.date == target_date
        )
    ).scalar_one_or_none()

    if ds is None:
        ds = DailyStat(
            brawler_id=brawler.id,
            date=target_date,
            reviews_count=reviews_count,
            achieved=False,
        )
        session.add(ds)
    else:
        if reviews_count > ds.reviews_count:
            ds.reviews_count = reviews_count

    was_achieved = ds.achieved
    will_achieve = ds.reviews_count >= daily_goal_threshold

    achievement_unlocked = False
    if will_achieve and not was_achieved:
        ds.achieved = True
        brawler.coins_total += 1

        yesterday_ds = session.execute(
            select(DailyStat).where(
                DailyStat.brawler_id == brawler.id,
                DailyStat.date == target_date - timedelta(days=1),
            )
        ).scalar_one_or_none()
        if yesterday_ds is not None and yesterday_ds.achieved:
            brawler.streak_current = brawler.streak_current + 1
        else:
            brawler.streak_current = 1
        if brawler.streak_current > brawler.streak_max:
            brawler.streak_max = brawler.streak_current
        achievement_unlocked = True

    session.flush()
    return StatsApplyResult(
        daily_stat=ds, brawler=brawler, achievement_unlocked=achievement_unlocked
    )
