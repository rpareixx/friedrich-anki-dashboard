# friedrich-anki-dashboard

Visualisierungs-Dashboard fuer Anki-Lernfortschritt der Familie Parei. Streak + Coin-Counter, Brawler-Avatars, VPS-Hosted via Cloudflare Tunnel.

Phase 4 von [friedrich-anki-evolution](../friedrich-schule). Siehe Vault-Doc `Obsidian/Claud_Obsidian/projects/friedrich-anki-evolution/phase-4-1a-robert-pilot.md` fuer den vollstaendigen Plan.

## Phase 4.1a Scope

- 1 User (Robert), 1 Brawler-Slot (Englisch), 1 Subdomain (`robert.parei.eu`)
- Multi-User-DB-Schema von Anfang (4.1b/c haengen drauf)
- Daten-Pipeline Mac → VPS (launchd nightly + post-review-hook)
- Statischer Brawler-Avatar (kein State-Wechsel, keine Animation)
- Bonus-Engine trivial: Tagesziel ≥ 20 Reviews → coins+1, streak+1
- Tagesziel-Schwelle als Tuning-Config

**Out-of-Scope:** Power-Up-Bank, Multiplikator, Power-Level-Bar, Telegram-Approval, Coin-Einlose-Mechanik. Reward-Mechanik kommt erst 4.1c mit Friedrich.

## Stack

- Backend: FastAPI + SQLAlchemy + Alembic
- DB: SQLite
- Frontend (Task 4): Astro Static + Alpine.js + Tailwind
- Hosting: VPS openclaw + Cloudflare Tunnel + Email-OTP Access
- Pipeline (Task 5): launchd am Mac, JWT-authenticated Push

## Setup (Dev)

```bash
uv sync
cp .env.example .env  # Werte anpassen
uv run alembic upgrade head
uv run pytest -v
uv run uvicorn dashboard.app:app --reload
```

## Migrations

```bash
uv run alembic upgrade head           # auf neuesten Stand
uv run alembic revision -m "..."      # neue Migration
uv run alembic downgrade -1           # eine Revision zurueck
```

## Tasks (Issues)

Phase 4.1a Tasks 1-7: siehe [Issues](https://github.com/rpareixx/friedrich-anki-dashboard/issues).

## Lizenz

Privat / kein Lizenz-Block.
