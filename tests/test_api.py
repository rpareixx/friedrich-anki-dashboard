from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dashboard import db as db_module
from dashboard.app import app
from dashboard.config import get_settings

PIPELINE_KEY = "test-pipeline-key"
DEV_TOKEN = "test-dev-token"


@pytest.fixture
def client(fresh_db: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("PIPELINE_API_KEY", PIPELINE_KEY)
    monkeypatch.setenv("DEV_TOKEN", DEV_TOKEN)
    monkeypatch.setenv("DAILY_GOAL_THRESHOLD", "20")
    get_settings.cache_clear()
    db_module.reset_engine_cache()

    SessionLocal = db_module.get_sessionmaker()

    def _override():
        s = SessionLocal()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[db_module.get_session] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _stats_payload(**overrides) -> dict:
    base = {
        "user_slug": "robert",
        "brawler_subject": "englisch",
        "date": "2026-05-08",
        "reviews_count": 25,
    }
    base.update(overrides)
    return base


def test_healthz_no_auth_required(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_post_stats_without_auth_returns_401(client: TestClient) -> None:
    r = client.post("/api/stats", json=_stats_payload())
    assert r.status_code == 401


def test_post_stats_wrong_token_returns_401(client: TestClient) -> None:
    r = client.post(
        "/api/stats",
        json=_stats_payload(),
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert r.status_code == 401


def test_post_stats_invalid_payload_returns_422(client: TestClient) -> None:
    r = client.post(
        "/api/stats",
        json={"user_slug": "robert"},
        headers={"Authorization": f"Bearer {PIPELINE_KEY}"},
    )
    assert r.status_code == 422


def test_post_stats_unknown_user_returns_404(client: TestClient) -> None:
    r = client.post(
        "/api/stats",
        json=_stats_payload(user_slug="unknown"),
        headers={"Authorization": f"Bearer {PIPELINE_KEY}"},
    )
    assert r.status_code == 404


def test_post_stats_unknown_brawler_returns_404(client: TestClient) -> None:
    r = client.post(
        "/api/stats",
        json=_stats_payload(brawler_subject="quantum-physics"),
        headers={"Authorization": f"Bearer {PIPELINE_KEY}"},
    )
    assert r.status_code == 404


def test_post_stats_success_below_threshold(client: TestClient) -> None:
    r = client.post(
        "/api/stats",
        json=_stats_payload(reviews_count=10),
        headers={"Authorization": f"Bearer {PIPELINE_KEY}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["reviews_count"] == 10
    assert body["achieved"] is False
    assert body["coins_total"] == 0
    assert body["streak_current"] == 0


def test_post_stats_success_unlocks_achievement(client: TestClient) -> None:
    r = client.post(
        "/api/stats",
        json=_stats_payload(reviews_count=25),
        headers={"Authorization": f"Bearer {PIPELINE_KEY}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["achieved"] is True
    assert body["coins_total"] == 1
    assert body["streak_current"] == 1


def test_post_stats_idempotent(client: TestClient) -> None:
    headers = {"Authorization": f"Bearer {PIPELINE_KEY}"}
    client.post("/api/stats", json=_stats_payload(reviews_count=25), headers=headers)
    r2 = client.post("/api/stats", json=_stats_payload(reviews_count=25), headers=headers)
    assert r2.status_code == 200
    body = r2.json()
    assert body["coins_total"] == 1
    assert body["streak_current"] == 1


def test_get_state_without_auth_returns_401(client: TestClient) -> None:
    r = client.get("/api/state/robert/englisch")
    assert r.status_code == 401


def test_get_state_with_dev_token(client: TestClient) -> None:
    r = client.get(
        "/api/state/robert/englisch",
        headers={"Authorization": f"Bearer {DEV_TOKEN}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["user_slug"] == "robert"
    assert body["brawler_subject"] == "englisch"
    assert body["coins_total"] == 0
    assert body["streak_current"] == 0


def test_get_state_unknown_user_returns_404(client: TestClient) -> None:
    r = client.get(
        "/api/state/unknown/englisch",
        headers={"Authorization": f"Bearer {DEV_TOKEN}"},
    )
    assert r.status_code == 404


def test_get_state_unknown_brawler_returns_404(client: TestClient) -> None:
    r = client.get(
        "/api/state/robert/quantum-physics",
        headers={"Authorization": f"Bearer {DEV_TOKEN}"},
    )
    assert r.status_code == 404


def test_get_state_with_cf_access_email_match(client: TestClient) -> None:
    r = client.get(
        "/api/state/robert/englisch",
        headers={"Cf-Access-Authenticated-User-Email": "robert.parei@parei.eu"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["user_slug"] == "robert"


def test_get_state_with_cf_access_email_mismatch_returns_403(
    client: TestClient,
) -> None:
    r = client.get(
        "/api/state/robert/englisch",
        headers={"Cf-Access-Authenticated-User-Email": "stranger@example.com"},
    )
    assert r.status_code == 403


def test_post_stats_then_get_state_reflects(client: TestClient) -> None:
    headers = {"Authorization": f"Bearer {PIPELINE_KEY}"}
    today = date.today().isoformat()
    client.post(
        "/api/stats",
        json=_stats_payload(date=today, reviews_count=42),
        headers=headers,
    )
    r = client.get(
        "/api/state/robert/englisch",
        headers={"Authorization": f"Bearer {DEV_TOKEN}"},
    )
    body = r.json()
    assert body["reviews_today"] == 42
    assert body["achieved_today"] is True
    assert body["coins_total"] == 1
    assert body["streak_current"] == 1
