import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from dashboard.routes import health, state, stats

app = FastAPI(title="friedrich-anki-dashboard", version="0.1.0")

app.include_router(health.router)
app.include_router(stats.router)
app.include_router(state.router)


def _find_dir(env_key: str, *fallbacks: Path) -> Path | None:
    candidates = [Path(os.environ.get(env_key, "")), *fallbacks]
    for p in candidates:
        if p and p.exists() and p.is_dir():
            return p
    return None


_assets = _find_dir(
    "ASSETS_DIR",
    Path("/app/assets"),
    Path(__file__).resolve().parents[2] / "assets",
)
if _assets is not None:
    app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

_dist = _find_dir(
    "FRONTEND_DIST",
    Path("/app/frontend/dist"),
    Path(__file__).resolve().parents[2] / "frontend" / "dist",
)
if _dist is not None:
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="frontend")
