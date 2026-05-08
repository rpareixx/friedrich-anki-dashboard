from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dashboard.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Berlin")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    brawlers: Mapped[list["Brawler"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Brawler(Base):
    __tablename__ = "brawlers"
    __table_args__ = (UniqueConstraint("user_id", "slot", name="uq_brawlers_user_slot"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    slot: Mapped[int] = mapped_column(Integer, nullable=False)
    subject: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    coins_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    streak_current: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    streak_max: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    user: Mapped[User] = relationship(back_populates="brawlers")
    daily_stats: Mapped[list["DailyStat"]] = relationship(
        back_populates="brawler", cascade="all, delete-orphan"
    )


class DailyStat(Base):
    __tablename__ = "daily_stats"
    __table_args__ = (UniqueConstraint("brawler_id", "date", name="uq_daily_stats_brawler_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brawler_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("brawlers.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    reviews_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    achieved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    brawler: Mapped[Brawler] = relationship(back_populates="daily_stats")
