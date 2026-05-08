"""dashboard-pipeline CLI — Mac-seitiger Push zu /api/stats."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date as date_cls
from typing import Sequence

import httpx

from dashboard.pipeline.anki import (
    DEFAULT_ANKI_URL,
    AnkiConnect,
    AnkiConnectError,
    reviews_in_local_day,
)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="dashboard-pipeline")
    sub = p.add_subparsers(dest="command", required=True)

    for name in ("push", "dry-run"):
        s = sub.add_parser(name)
        s.add_argument("--user", default="robert")
        s.add_argument("--subject", default="englisch")
        s.add_argument("--deck", default="Sprachen::Robert::Englisch")
        s.add_argument("--date", default=None, help="ISO date, default: today (local TZ)")
        s.add_argument("--timezone", default=os.environ.get("TIMEZONE", "Europe/Berlin"))
        s.add_argument(
            "--anki-url",
            default=os.environ.get("ANKI_CONNECT_URL", DEFAULT_ANKI_URL),
        )
        s.add_argument(
            "--dashboard-url",
            default=os.environ.get("DASHBOARD_API_URL", "http://localhost:8000"),
        )
        s.add_argument(
            "--api-key",
            default=os.environ.get("PIPELINE_API_KEY"),
            help="overrides PIPELINE_API_KEY env var",
        )

    return p.parse_args(argv)


def build_payload(args: argparse.Namespace) -> dict:
    target_date = (
        date_cls.fromisoformat(args.date)
        if args.date
        else _local_today(args.timezone)
    )
    anki = AnkiConnect(args.anki_url)
    reviews = reviews_in_local_day(anki, args.deck, target_date, args.timezone)
    return {
        "user_slug": args.user,
        "brawler_subject": args.subject,
        "date": target_date.isoformat(),
        "reviews_count": reviews,
    }


def push(payload: dict, dashboard_url: str, api_key: str) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"}
    cf_id = os.environ.get("CF_ACCESS_CLIENT_ID")
    cf_secret = os.environ.get("CF_ACCESS_CLIENT_SECRET")
    if cf_id and cf_secret:
        headers["CF-Access-Client-Id"] = cf_id
        headers["CF-Access-Client-Secret"] = cf_secret
    r = httpx.post(
        f"{dashboard_url.rstrip('/')}/api/stats",
        json=payload,
        headers=headers,
        timeout=30.0,
    )
    r.raise_for_status()
    return r.json()


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        payload = build_payload(args)
    except AnkiConnectError as exc:
        print(f"error: cannot reach AnkiConnect at {args.anki_url}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.command == "dry-run":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if not args.api_key:
        print(
            "error: --api-key or PIPELINE_API_KEY env var required for push",
            file=sys.stderr,
        )
        return 2

    try:
        response = push(payload, args.dashboard_url, args.api_key)
    except httpx.HTTPStatusError as exc:
        print(
            f"error: dashboard returned {exc.response.status_code}: {exc.response.text}",
            file=sys.stderr,
        )
        return 1
    except httpx.HTTPError as exc:
        print(f"error: cannot reach dashboard at {args.dashboard_url}: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0


def _local_today(tz_name: str) -> date_cls:
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo(tz_name)).date()


if __name__ == "__main__":
    sys.exit(main())
