"""
Prediction Service
Orchestrates: weather data fetch → feature engineering → ML inference → DB store
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import httpx

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.config import settings
from app.ml.ensemble import EnsemblePredictor
from app.models.db_models import WeatherObservation, HeatwavePrediction, DistrictProfile

logger = logging.getLogger(__name__)

# Shared ensemble predictor (loaded once at startup)
_predictor: Optional[EnsemblePredictor] = None


def get_predictor() -> EnsemblePredictor:
    global _predictor
    if _predictor is None:
        _predictor = EnsemblePredictor()
    return _predictor


# Sample district profiles for demo
DEMO_DISTRICTS = {
    "Vijayawada": {
        "district": "Vijayawada", "state": "Andhra Pradesh",
        "latitude": 16.5062, "longitude": 80.6480,
        "population": 1048240, "elderly_population_pct": 0.09,
        "children_population_pct": 0.17, "green_cover_pct": 0.15,
        "urban_area_pct": 0.72, "uhi_score": 0.65,
        "cooling_centres": [
            {"name": "Gandhi Hill Community Centre", "lat": 16.514, "lng": 80.634},
            {"name": "Indira Gandhi Municipal Stadium", "lat": 16.508, "lng": 80.655},
        ],
    },
    "Hyderabad": {
        "district": "Hyderabad", "state": "Telangana",
        "latitude": 17.3850, "longitude": 78.4867,
        "population": 6731790, "elderly_population_pct": 0.08,
        "children_population_pct": 0.19, "green_cover_pct": 0.12,
        "urban_area_pct": 0.85, "uhi_score": 0.78,
        "cooling_centres": [
            {"name": "Hyderabad Exhibition Grounds", "lat": 17.408, "lng": 78.468},
            {"name": "GHMC Cooling Centre - Secunderabad", "lat": 17.440, "lng": 78.499},
        ],
    },
    "Chennai": {
        "district": "Chennai", "state": "Tamil Nadu",
        "latitude": 13.0827, "longitude": 80.2707,
        "population": 7088000, "elderly_population_pct": 0.10,
        "children_population_pct": 0.16, "green_cover_pct": 0.11,
        "urban_area_pct": 0.90, "uhi_score": 0.80,
        "cooling_centres": [
            {"name": "Marina Beach Shelter", "lat": 13.062, "lng": 80.277},
        ],
    },
}


class PredictionService:
    """Service that orchestrates the full prediction pipeline."""

    def __init__(self):
        self.predictor = get_predictor()

    async def run_prediction(
        self,
        district: str,
        state: str,
        latitude: float,
        longitude: float,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """Full prediction pipeline for a district."""

        # 1. Get district info
        district_info = DEMO_DISTRICTS.get(district, {
            "district": district,
            "state": state,
            "latitude": latitude,
            "longitude": longitude,
            "population": 500000,
            "elderly_population_pct": 0.10,
            "children_population_pct": 0.18,
            "green_cover_pct": 0.20,
            "urban_area_pct": 0.55,
            "uhi_score": 0.50,
            "cooling_centres": [],
        })

        # 2. Fetch recent weather (try API, fallback to synthetic)
        recent_weather = await self._fetch_weather_data(latitude, longitude)

        # 3. Run ensemble
        result = self.predictor.predict(recent_weather, district_info)

        # 4. Save to database
        await self._save_prediction(result, db)

        return result

    async def _fetch_weather_data(self, lat: float, lon: float) -> pd.DataFrame:
        """Fetch 30-day weather history from OpenWeather API."""
        if not settings.OPENWEATHER_API_KEY:
            logger.info("No API key — generating synthetic weather data")
            return self._generate_mock_weather(lat, lon)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.openweathermap.org/data/2.5/forecast",
                    params={
                        "lat": lat, "lon": lon,
                        "appid": settings.OPENWEATHER_API_KEY,
                        "units": "metric",
                        "cnt": 40,
                    }
                )
                data = resp.json()
                records = []
                for item in data.get("list", []):
                    records.append({
                        "date": item["dt_txt"][:10],
                        "temp_max": item["main"]["temp_max"],
                        "temp_min": item["main"]["temp_min"],
                        "humidity": item["main"]["humidity"],
                        "wind_speed": item["wind"]["speed"] * 3.6,
                        "pressure": item["main"]["pressure"],
                        "heat_index": item["main"]["feels_like"],
                        "uhi_score": 0.5,
                    })
                return pd.DataFrame(records)
        except Exception as e:
            logger.warning(f"Weather API failed: {e} — using synthetic data")
            return self._generate_mock_weather(lat, lon)

    def _generate_mock_weather(self, lat: float, lon: float) -> pd.DataFrame:
        """Generate 35 days of realistic synthetic weather for inference."""
        np.random.seed(int(abs(lat * lon) % 1000))
        n = 35
        dates = pd.date_range(end=datetime.now(), periods=n)
        doy = np.array([d.timetuple().tm_yday for d in dates])
        seasonal = 30 + 12 * np.sin(2 * np.pi * (doy - 90) / 365)

        return pd.DataFrame({
            "date": dates.strftime("%Y-%m-%d"),
            "temp_max": np.round(seasonal + np.random.normal(0, 2.5, n), 1),
            "temp_min": np.round(seasonal - 8 + np.random.normal(0, 1.5, n), 1),
            "humidity": np.round(np.clip(55 + np.random.normal(0, 10, n), 20, 90), 1),
            "wind_speed": np.round(np.abs(np.random.normal(12, 4, n)), 1),
            "pressure": np.round(1010 + np.random.normal(0, 4, n), 1),
            "heat_index": np.round(seasonal + 3 + np.random.normal(0, 2, n), 1),
            "uhi_score": np.round(np.random.uniform(0.4, 0.7, n), 2),
        })

    async def _save_prediction(self, result: Dict, db: AsyncSession):
        """Persist prediction to database."""
        try:
            for day in result["forecast"]:
                pred = HeatwavePrediction(
                    district=result["district"],
                    state=result["state"],
                    prediction_date=datetime.now(),
                    target_date=datetime.strptime(day["date"], "%Y-%m-%d"),
                    forecast_day=day["day"],
                    predicted_temp_max=day["predicted_temp_max"],
                    predicted_temp_min=day["predicted_temp_min"],
                    temp_confidence_lower=day["confidence_lower"],
                    temp_confidence_upper=day["confidence_upper"],
                    heatwave_probability=day["heatwave_probability"],
                    is_heatwave=day["is_heatwave"],
                    severity=day["severity"],
                    severity_score=day["severity_score"],
                    ensemble_confidence=result["ensemble_confidence"],
                    alert_triggered=result["alert_required"],
                    shap_values=result.get("top_risk_factors", []),
                )
                db.add(pred)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to save prediction: {e}")

    async def get_all_district_risks(self, db: AsyncSession) -> List[Dict]:
        """Get risk summary for all demo districts."""
        results = []
        for district, info in DEMO_DISTRICTS.items():
            np.random.seed(hash(district) % 1000)
            severity_options = ["none", "mild", "moderate", "severe", "extreme"]
            sev = np.random.choice(severity_options, p=[0.3, 0.3, 0.2, 0.15, 0.05])
            results.append({
                "district": district,
                "state": info["state"],
                "latitude": info["latitude"],
                "longitude": info["longitude"],
                "current_severity": sev,
                "max_predicted_temp": round(np.random.uniform(36, 46), 1),
                "heatwave_probability": round(np.random.uniform(0.2, 0.9), 2),
                "vulnerable_population": int(
                    info["population"] * (info["elderly_population_pct"] + info["children_population_pct"])
                ),
                "risk_score": round(np.random.uniform(20, 90), 1),
            })
        return results

    async def get_latest_forecast(self, district: str, db: AsyncSession) -> Dict:
        """Get latest stored forecast for district."""
        stmt = select(HeatwavePrediction).where(
            HeatwavePrediction.district == district
        ).order_by(desc(HeatwavePrediction.created_at)).limit(7)
        result = await db.execute(stmt)
        records = result.scalars().all()
        return {"district": district, "forecast": [r.__dict__ for r in records]}

    async def get_history(self, district: str, days: int, db: AsyncSession) -> List[Dict]:
        """Get prediction history."""
        return []  # Placeholder — implement with real DB query
