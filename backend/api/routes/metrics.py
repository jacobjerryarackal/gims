from fastapi import APIRouter
from services.health_service import health_service

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("")
async def get_metrics():
    return await health_service.get_metrics()
