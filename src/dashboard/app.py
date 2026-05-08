"""FastAPI-App stub. Vollstaendige Endpoints kommen in Task 3 (Issue #3)."""
from fastapi import FastAPI

app = FastAPI(title="friedrich-anki-dashboard", version="0.1.0")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
