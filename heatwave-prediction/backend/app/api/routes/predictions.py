"""Predictions API router."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import pandas as pd
import logging

from app.core.database import get_db
from app.models.schemas import PredictionRequest, PredictionResponse
from app.services.prediction_service import PredictionService
from app.services.alert_service import AlertService

router = APIRouter()
logger = logging.getLogger(__name__)

prediction_service = PredictionService()
alert_service = AlertService()


@router.post("/predict", response_model=PredictionResponse, summary="Run heatwave prediction")
async def predict_heatwave(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Run full 7-day heatwave prediction for a district.
    
    Uses the 4-model ML ensemble:
    - LSTM temperature forecaster
    - XGBoost onset classifier  
    - Random Forest severity scorer
    - SHAP explainability
    
    Automatically triggers alerts if confidence > 70%.
    """
    try:
        result = await prediction_service.run_prediction(
            district=request.district,
            state=request.state,
            latitude=request.latitude,
            longitude=request.longitude,
            db=db,
        )

        # Trigger alerts in background if required
        if result.get("alert_required"):
            background_tasks.add_task(
                alert_service.send_heatwave_alert,
                district=request.district,
                prediction=result,
            )

        return result

    except Exception as e:
        logger.error(f"Prediction failed for {request.district}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/districts", summary="Get risk summary for all districts")
async def get_all_district_risks(db: AsyncSession = Depends(get_db)):
    """Get current heatwave risk summary for all monitored districts."""
    try:
        return await prediction_service.get_all_district_risks(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/{district}/history", summary="Get prediction history for a district")
async def get_prediction_history(
    district: str,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get historical predictions for model performance analysis."""
    try:
        return await prediction_service.get_history(district, days, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predict/{district}/forecast", summary="Get latest forecast for district")
async def get_district_forecast(district: str, db: AsyncSession = Depends(get_db)):
    """Get the latest 7-day forecast for a specific district."""
    try:
        return await prediction_service.get_latest_forecast(district, db)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"No forecast found for {district}")
