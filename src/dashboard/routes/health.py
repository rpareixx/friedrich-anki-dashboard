from fastapi import APIRouter

from dashboard.schemas import HealthOut

router = APIRouter()


@router.get("/healthz", response_model=HealthOut)
async def healthz() -> HealthOut:
    return HealthOut(status="ok")
