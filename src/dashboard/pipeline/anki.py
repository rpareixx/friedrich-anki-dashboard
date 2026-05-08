"""Minimal AnkiConnect client for the pipeline.

Self-contained — does not depend on anki-bridge to keep this repo
deployable in isolation.
"""
from __future__ import annotations

from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

import httpx

DEFAULT_ANKI_URL = "http://127.0.0.1:8765"


class AnkiConnectError(RuntimeError):
    pass


class AnkiConnect:
    def __init__(self, url: str = DEFAULT_ANKI_URL, timeout: float = 30.0) -> None:
        self.url = url
        self.timeout = timeout

    def call(self, action: str, **params: Any) -> Any:
        payload = {"action": action, "version": 6, "params": params}
        try:
            r = httpx.post(self.url, json=payload, timeout=self.timeout)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise AnkiConnectError(f"AnkiConnect HTTP error: {exc}") from exc
        body = r.json()
        if body.get("error"):
            raise AnkiConnectError(f"AnkiConnect error: {body['error']}")
        return body.get("result")

    def card_reviews_since(self, deck: str, since_ms: int) -> list[list[int]]:
        return self.call("cardReviews", deck=deck, startID=since_ms) or []


def reviews_in_local_day(
    anki: AnkiConnect, deck: str, target_day: date, tz_name: str
) -> int:
    """Number of reviews posted on `target_day` (local TZ) for `deck`."""
    tz = ZoneInfo(tz_name)
    day_start = datetime.combine(target_day, time.min, tzinfo=tz)
    day_end = datetime.combine(target_day, time.max, tzinfo=tz)
    start_ms = int(day_start.timestamp() * 1000)
    end_ms = int(day_end.timestamp() * 1000)

    reviews = anki.card_reviews_since(deck, since_ms=start_ms)
    # AnkiConnect cardReviews schema: r[0] is the review timestamp (ms).
    # r[4] is lastIvl (interval), NOT a timestamp — using it would always return 0.
    return sum(1 for r in reviews if len(r) >= 1 and start_ms <= int(r[0]) <= end_ms)
