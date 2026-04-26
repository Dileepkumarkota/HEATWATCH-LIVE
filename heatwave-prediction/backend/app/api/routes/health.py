"""Health check, alerts, explain, data, and websocket routes."""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Heatwave Prediction System",
        "version": "1.0.0",
    }
