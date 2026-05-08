"""Pipeline tests — uses respx to mock AnkiConnect + dashboard backend."""
from __future__ import annotations

from datetime import date, datetime, time
from unittest.mock import patch
from zoneinfo import ZoneInfo

import httpx
import pytest

from dashboard.pipeline.anki import AnkiConnect, AnkiConnectError, reviews_in_local_day
from dashboard.pipeline.cli import main as pipeline_main


def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _mock_anki_response(result):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": result, "error": None})

    return httpx.MockTransport(handler)


def _mock_anki_error(error_msg: str):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"result": None, "error": error_msg})

    return httpx.MockTransport(handler)


def _mock_anki_http_error(status_code: int):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, text="boom")

    return httpx.MockTransport(handler)


def test_anki_connect_returns_result(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _mock_anki_response([1, 2, 3])
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: httpx.Client(transport=transport).post(*a, **kw))
    anki = AnkiConnect("http://test")
    assert anki.call("foo") == [1, 2, 3]


def test_anki_connect_raises_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _mock_anki_error("deck not found")
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: httpx.Client(transport=transport).post(*a, **kw))
    anki = AnkiConnect("http://test")
    with pytest.raises(AnkiConnectError, match="deck not found"):
        anki.call("foo")


def test_anki_connect_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _mock_anki_http_error(500)
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: httpx.Client(transport=transport).post(*a, **kw))
    anki = AnkiConnect("http://test")
    with pytest.raises(AnkiConnectError, match="HTTP error"):
        anki.call("foo")


def test_reviews_in_local_day_counts_within_window(monkeypatch: pytest.MonkeyPatch) -> None:
    tz = ZoneInfo("Europe/Berlin")
    today = date(2026, 5, 8)
    in_window = _ms(datetime.combine(today, time(10, 30), tzinfo=tz))
    yesterday = _ms(datetime.combine(date(2026, 5, 7), time(23, 0), tzinfo=tz))
    tomorrow = _ms(datetime.combine(date(2026, 5, 9), time(0, 30), tzinfo=tz))

    # AnkiConnect cardReviews schema: r[0] is the review timestamp (ms)
    reviews = [
        [in_window, 2, 3, 4, 5],
        [in_window + 1000, 2, 3, 4, 5],
        [in_window + 2000, 2, 3, 4, 5],
        [yesterday, 2, 3, 4, 5],  # outside (older than start)
        [tomorrow, 2, 3, 4, 5],  # outside (after end)
    ]
    transport = _mock_anki_response(reviews)
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: httpx.Client(transport=transport).post(*a, **kw))

    anki = AnkiConnect("http://test")
    count = reviews_in_local_day(anki, "Test::Deck", today, "Europe/Berlin")
    assert count == 3


def test_reviews_in_local_day_zero_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    transport = _mock_anki_response([])
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: httpx.Client(transport=transport).post(*a, **kw))
    anki = AnkiConnect("http://test")
    count = reviews_in_local_day(anki, "Empty::Deck", date(2026, 5, 8), "Europe/Berlin")
    assert count == 0


def test_dry_run_prints_json_and_exits_0(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    tz = ZoneInfo("Europe/Berlin")
    today = date(2026, 5, 8)
    in_window = _ms(datetime.combine(today, time(10, 30), tzinfo=tz))
    transport = _mock_anki_response([[in_window, 2, 3, 4, 5]] * 5)
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: httpx.Client(transport=transport).post(*a, **kw))

    rc = pipeline_main(
        [
            "dry-run",
            "--user",
            "robert",
            "--subject",
            "englisch",
            "--deck",
            "Test::Deck",
            "--date",
            "2026-05-08",
            "--timezone",
            "Europe/Berlin",
            "--anki-url",
            "http://test",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    import json as _json
    payload = _json.loads(out)
    assert payload == {
        "user_slug": "robert",
        "brawler_subject": "englisch",
        "date": "2026-05-08",
        "reviews_count": 5,
    }


def test_dry_run_does_not_post_to_dashboard(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify dry-run never hits dashboard URL."""
    tz = ZoneInfo("Europe/Berlin")
    today = date(2026, 5, 8)
    in_window = _ms(datetime.combine(today, time(10, 30), tzinfo=tz))

    posts: list[str] = []

    def fake_post(url, *args, **kwargs):
        posts.append(url)
        if "test-anki" in url:
            return httpx.Client(
                transport=_mock_anki_response([[in_window, 2, 3, 4, 5]])
            ).post(url, *args, **kwargs)
        raise AssertionError(f"unexpected POST to {url}")

    monkeypatch.setattr(httpx, "post", fake_post)

    rc = pipeline_main(
        [
            "dry-run",
            "--anki-url",
            "http://test-anki",
            "--dashboard-url",
            "http://should-not-be-called",
            "--date",
            "2026-05-08",
            "--deck",
            "Test::Deck",
        ]
    )
    assert rc == 0
    assert all("test-anki" in u for u in posts), posts


def test_push_returns_2_on_anki_unreachable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_post(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", fake_post)

    rc = pipeline_main(
        [
            "push",
            "--user",
            "robert",
            "--subject",
            "englisch",
            "--anki-url",
            "http://localhost:9999",
            "--api-key",
            "test-key",
            "--date",
            "2026-05-08",
            "--deck",
            "Test::Deck",
        ]
    )
    assert rc == 2
    assert "AnkiConnect" in capsys.readouterr().err


def test_push_requires_api_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    tz = ZoneInfo("Europe/Berlin")
    today = date(2026, 5, 8)
    in_window = _ms(datetime.combine(today, time(10, 30), tzinfo=tz))
    transport = _mock_anki_response([[in_window, 2, 3, 4, 5]])
    monkeypatch.setattr(httpx, "post", lambda *a, **kw: httpx.Client(transport=transport).post(*a, **kw))
    monkeypatch.delenv("PIPELINE_API_KEY", raising=False)

    rc = pipeline_main(
        [
            "push",
            "--anki-url",
            "http://test",
            "--date",
            "2026-05-08",
            "--deck",
            "Test::Deck",
        ]
    )
    assert rc == 2
    assert "api-key" in capsys.readouterr().err.lower()
