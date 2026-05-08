from fastapi import FastAPI

from dashboard.routes import health, state, stats

app = FastAPI(title="friedrich-anki-dashboard", version="0.1.0")

app.include_router(health.router)
app.include_router(stats.router)
app.include_router(state.router)
