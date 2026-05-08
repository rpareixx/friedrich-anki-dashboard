from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class StatsPushIn(BaseModel):
    user_slug: str = Field(..., min_length=1, max_length=64)
    brawler_subject: str = Field(..., min_length=1, max_length=64)
    date: date
    reviews_count: int = Field(..., ge=0)


class StatsPushOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    reviews_count: int
    achieved: bool
    coins_total: int
    streak_current: int
    streak_max: int


class BrawlerStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_slug: str
    brawler_subject: str
    asset_path: str | None
    coins_total: int
    streak_current: int
    streak_max: int
    reviews_today: int
    achieved_today: bool
    today: date
    updated_at: datetime


class HealthOut(BaseModel):
    status: str
