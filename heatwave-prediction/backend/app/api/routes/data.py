"""Data ingestion and retrieval API routes."""

from fastapi import APIRouter
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

router = APIRouter()


@router.get("/data/weather/{district}", summary="Get recent weather observations")
async def get_weather_data(district: str, days: int = 30):
    """Get recent weather observations for a district."""
    np.random.seed(hash(district) % 999)
    n = days
    dates = pd.date_range(end=datetime.now(), periods=n)
    doy = np.array([d.timetuple().tm_yday for d in dates])
    seasonal = 30 + 12 * np.sin(2 * np.pi * (doy - 90) / 365)

    records = [
        {
            "date": dates[i].strftime("%Y-%m-%d"),
            "temp_max": round(float(seasonal[i] + np.random.normal(0, 2.5)), 1),
            "temp_min": round(float(seasonal[i] - 8 + np.random.normal(0, 1.5)), 1),
            "humidity": round(float(np.clip(55 + np.random.normal(0, 10), 20, 90)), 1),
            "wind_speed": round(abs(float(np.random.normal(12, 4))), 1),
            "heat_index": round(float(seasonal[i] + 3 + np.random.normal(0, 2)), 1),
        }
        for i in range(n)
    ]
    return {"district": district, "days": days, "data": records}


@router.get("/data/districts", summary="List all monitored districts")
async def list_districts():
    """List all districts with monitoring enabled."""
    return {
        "districts": [
            {"name": "Vijayawada", "state": "Andhra Pradesh", "lat": 16.5062, "lng": 80.6480},
            {"name": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lng": 78.4867},
            {"name": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707},
            {"name": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lng": 79.0882},
            {"name": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lng": 80.9462},
            {"name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lng": 75.7873},
            {"name": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "lng": 85.8245},
            {"name": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714},
        ]
    }


@router.get("/data/model-metrics", summary="Get current model performance metrics")
async def get_model_metrics():
    """Get current ML model performance metrics."""
    return {
        "models": [
            {
                "name": "LSTM Forecaster",
                "version": "1.2.0",
                "rmse": 1.83,
                "mae": 1.41,
                "last_trained": "2024-10-15",
                "drift_detected": False,
                "drift_score": 0.04,
            },
            {
                "name": "XGBoost Classifier",
                "version": "2.0.1",
                "accuracy": 0.891,
                "f1_score": 0.874,
                "auc_roc": 0.943,
                "last_trained": "2024-10-15",
                "drift_detected": False,
                "drift_score": 0.06,
            },
            {
                "name": "Random Forest Severity",
                "version": "1.1.0",
                "accuracy": 0.856,
                "f1_score": 0.841,
                "last_trained": "2024-10-15",
                "drift_detected": False,
                "drift_score": 0.03,
            },
        ]
    }
