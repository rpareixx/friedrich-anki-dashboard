import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from dashboard.routes import health, state, stats

app = FastAPI(title="friedrich-anki-dashboard", version="0.1.0")

app.include_router(health.router)
app.include_router(stats.router)
app.include_router(state.router)


def _frontend_dist() -> Path | None:
    candidates = [
        Path(os.environ.get("FRONTEND_DIST", "")),
        Path("/app/frontend/dist"),
        Path(__file__).resolve().parents[2] / "frontend" / "dist",
    ]
    for p in candidates:
        if p and p.exists() and p.is_dir():
            return p
    return None


_dist = _frontend_dist()
if _dist is not None:
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
