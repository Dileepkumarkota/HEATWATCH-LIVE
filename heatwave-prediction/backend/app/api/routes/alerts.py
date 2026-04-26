"""Alerts API router."""

from fastapi import APIRouter, HTTPException
from app.models.schemas import AlertRequest, AlertResponse
from app.services.alert_service import AlertService
from datetime import datetime

router = APIRouter()
alert_service = AlertService()


@router.post("/alerts/send", response_model=AlertResponse, summary="Send heatwave alert")
async def send_alert(request: AlertRequest):
    """Manually trigger a heatwave alert to specified recipients."""
    try:
        result = await alert_service.send_heatwave_alert(
            district=request.district,
            prediction={"forecast": [], "health_risk": {}, "ensemble_confidence": 0.85,
                        "recommended_actions": ["Activate cooling centres", "Issue public advisory"]},
        )
        return AlertResponse(
            alert_id=1,
            status="sent",
            sent_to=request.recipients,
            message=f"Heatwave alert sent for {request.district}",
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/history", summary="Get alert history")
async def get_alert_history(district: str = None, limit: int = 50):
    """Get history of sent alerts."""
    return {"alerts": [], "total": 0}
