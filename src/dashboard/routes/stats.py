from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from dashboard.auth import require_pipeline_token
from dashboard.bonus_engine import apply_stats
from dashboard.config import Settings, get_settings
from dashboard.db import get_session
from dashboard.schemas import StatsPushIn, StatsPushOut

router = APIRouter(prefix="/api", tags=["stats"])


@router.post(
    "/stats",
    response_model=StatsPushOut,
    dependencies=[Depends(require_pipeline_token)],
)
def push_stats(
    payload: StatsPushIn,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> StatsPushOut:
    try:
        result = apply_stats(
            session=session,
            user_slug=payload.user_slug,
            brawler_subject=payload.brawler_subject,
            target_date=payload.date,
            reviews_count=payload.reviews_count,
            daily_goal_threshold=settings.daily_goal_threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    session.commit()
    session.refresh(result.daily_stat)
    session.refresh(result.brawler)

    return StatsPushOut(
        date=result.daily_stat.date,
        reviews_count=result.daily_stat.reviews_count,
        achieved=result.daily_stat.achieved,
        coins_total=result.brawler.coins_total,
        streak_current=result.brawler.streak_current,
        streak_max=result.brawler.streak_max,
    )
