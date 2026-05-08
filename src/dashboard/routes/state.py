from datetime import date as date_cls
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from dashboard.auth import require_state_access
from dashboard.config import Settings, get_settings
from dashboard.db import get_session
from dashboard.models import Brawler, DailyStat, User
from dashboard.schemas import BrawlerStateOut

router = APIRouter(prefix="/api", tags=["state"])


@router.get("/state/{user_slug}/{brawler_subject}", response_model=BrawlerStateOut)
def get_state(
    brawler_subject: str,
    user: User = Depends(require_state_access),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> BrawlerStateOut:
    brawler = session.execute(
        select(Brawler).where(
            Brawler.user_id == user.id, Brawler.subject == brawler_subject
        )
    ).scalar_one_or_none()
    if brawler is None:
        raise HTTPException(status_code=404, detail="brawler not found")

    today = _local_today(user.timezone or settings.timezone)
    today_stat = session.execute(
        select(DailyStat).where(
            DailyStat.brawler_id == brawler.id, DailyStat.date == today
        )
    ).scalar_one_or_none()

    return BrawlerStateOut(
        user_slug=user.slug,
        brawler_subject=brawler.subject,
        asset_path=brawler.asset_path,
        coins_total=brawler.coins_total,
        streak_current=brawler.streak_current,
        streak_max=brawler.streak_max,
        reviews_today=today_stat.reviews_count if today_stat else 0,
        achieved_today=today_stat.achieved if today_stat else False,
        today=today,
        updated_at=brawler.updated_at,
    )


def _local_today(tz_name: str) -> date_cls:
    from datetime import datetime

    return datetime.now(ZoneInfo(tz_name)).date()
