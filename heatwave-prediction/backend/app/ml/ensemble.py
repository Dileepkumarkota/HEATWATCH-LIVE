"""
Ensemble Prediction Service
Combines LSTM + XGBoost + Random Forest into a unified heatwave prediction.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from app.ml.lstm_model import LSTMForecastService
from app.ml.xgboost_classifier import XGBoostClassifier
from app.ml.severity_model import SeverityScorer
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnsemblePredictor:
    """
    Stacking ensemble that combines:
    - LSTM: temperature sequences (7-day)
    - XGBoost: heatwave onset probability
    - Random Forest: severity classification
    
    Outputs unified prediction with SHAP explanations.
    """

    def __init__(self):
        self.lstm = LSTMForecastService(settings.LSTM_MODEL_PATH)
        self.xgb = XGBoostClassifier(settings.XGBOOST_MODEL_PATH)
        self.rf = SeverityScorer(settings.RF_MODEL_PATH)
        logger.info("✅ Ensemble predictor initialized")

    def predict(
        self,
        recent_weather: pd.DataFrame,
        district_info: Dict[str, Any],
        normals_df: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        Run full ensemble prediction pipeline.
        
        Args:
            recent_weather: 30+ days of weather observations
            district_info: demographic data for health risk
            normals_df: climatological normals for anomaly computation
            
        Returns:
            Complete prediction with 7-day forecast, severity, SHAP, health risk
        """
        district = district_info.get("district", "Unknown")
        logger.info(f"🔮 Running ensemble prediction for {district}")

        # 1. LSTM — temperature sequences
        try:
            lstm_result = self.lstm.predict(recent_weather)
        except Exception as e:
            logger.warning(f"LSTM failed: {e} — using fallback temperatures")
            lstm_result = self._fallback_temperatures(recent_weather)

        # 2. XGBoost — onset classification + SHAP
        try:
            xgb_result = self.xgb.predict(recent_weather, normals_df)
        except Exception as e:
            logger.warning(f"XGBoost failed: {e}")
            latest_temp = recent_weather["temp_max"].iloc[-1]
            xgb_result = {
                "heatwave_probability": float(latest_temp >= 40) * 0.7,
                "is_heatwave": latest_temp >= 40,
                "top_shap_features": [],
            }

        # 3. Build day-by-day forecast
        forecast = []
        base_date = datetime.now()
        hw_prob = xgb_result["heatwave_probability"]

        for day in range(settings.FORECAST_DAYS):
            target_date = base_date + timedelta(days=day + 1)
            pred_temp = lstm_result["temp_max"][day]
            pred_temp_min = lstm_result["temp_min"][day]

            # Probability decays slightly with forecast horizon
            day_prob = hw_prob * (0.95 ** day)
            is_hw = bool(day_prob >= 0.50 and pred_temp >= 38)

            # Severity for this day
            sev_features = {
                "predicted_temp_max": pred_temp,
                "temp_max_anomaly": pred_temp - recent_weather["temp_max"].mean(),
                "heat_index": pred_temp * 1.05,
                "humidity": recent_weather["humidity"].iloc[-1],
                "consecutive_hot_days": float(day + 1) if is_hw else 0,
                "uhi_score": district_info.get("uhi_score", 0),
                "elderly_population_pct": district_info.get("elderly_population_pct", 0.12),
                "urban_area_pct": district_info.get("urban_area_pct", 0.5),
                "green_cover_pct": district_info.get("green_cover_pct", 0.2),
                "month": float(target_date.month),
                "duration_days": float(day + 1),
            }
            sev_result = self.rf.predict(sev_features)

            forecast.append({
                "date": target_date.strftime("%Y-%m-%d"),
                "day": day + 1,
                "predicted_temp_max": round(pred_temp, 1),
                "predicted_temp_min": round(pred_temp_min, 1),
                "confidence_lower": round(lstm_result["confidence_lower"][day], 1),
                "confidence_upper": round(lstm_result["confidence_upper"][day], 1),
                "heatwave_probability": round(day_prob, 3),
                "is_heatwave": is_hw,
                "severity": sev_result["severity"],
                "severity_score": round(sev_result["severity_score"], 3),
            })

        # 4. Ensemble confidence (weighted average)
        max_hw_prob = max(d["heatwave_probability"] for d in forecast)
        max_severity_score = max(d["severity_score"] for d in forecast)
        ensemble_confidence = round(
            0.5 * max_hw_prob + 0.3 * max_severity_score + 0.2 * (1 - hw_prob * 0.1),
            3
        )

        # 5. Health risk assessment
        health_risk = self._compute_health_risk(forecast, district_info)

        # 6. Alert required?
        alert_required = (
            ensemble_confidence >= settings.ALERT_CONFIDENCE_THRESHOLD
            and any(d["is_heatwave"] for d in forecast[:3])
        )

        return {
            "district": district,
            "state": district_info.get("state", ""),
            "prediction_date": base_date.strftime("%Y-%m-%d"),
            "forecast": forecast,
            "ensemble_confidence": ensemble_confidence,
            "alert_required": alert_required,
            "top_risk_factors": xgb_result.get("top_shap_features", []),
            "health_risk": health_risk,
            "cooling_centres": district_info.get("cooling_centres", []),
            "recommended_actions": self.rf.get_recommended_actions(
                max(forecast, key=lambda x: x["severity_score"])["severity"]
            ),
        }

    def _compute_health_risk(self, forecast: List[Dict], district_info: Dict) -> Dict:
        """Compute health impact based on prediction + demographics."""
        population = district_info.get("population", 100000)
        elderly_pct = district_info.get("elderly_population_pct", 0.12)
        children_pct = district_info.get("children_population_pct", 0.18)

        max_sev = max(forecast, key=lambda x: x["severity_score"])
        sev_score = max_sev["severity_score"]

        # Exposure factor: urban, low green cover = higher risk
        urban_pct = district_info.get("urban_area_pct", 0.5)
        green_pct = district_info.get("green_cover_pct", 0.2)
        exposure_factor = min(1.0, 0.5 + 0.3 * urban_pct - 0.2 * green_pct)

        vulnerable_pct = elderly_pct + children_pct
        vulnerable_pop = int(population * vulnerable_pct * sev_score * exposure_factor)

        risk_levels = {0: "low", 0.25: "moderate", 0.5: "high", 0.75: "very_high"}
        risk_level = "low"
        for threshold, level in sorted(risk_levels.items()):
            if sev_score >= threshold:
                risk_level = level

        return {
            "total_population": population,
            "vulnerable_population": vulnerable_pop,
            "elderly_at_risk": int(population * elderly_pct * sev_score * exposure_factor),
            "children_at_risk": int(population * children_pct * sev_score * exposure_factor),
            "risk_level": risk_level,
            "exposure_factor": round(exposure_factor, 2),
            "peak_severity": max_sev["severity"],
            "peak_date": max_sev["date"],
        }

    def _fallback_temperatures(self, df: pd.DataFrame) -> Dict:
        """Generate simple trend-based fallback when LSTM fails."""
        recent_temps = df["temp_max"].values[-7:]
        trend = np.polyfit(range(len(recent_temps)), recent_temps, 1)[0]
        base = recent_temps[-1]
        preds = [base + trend * (i + 1) for i in range(7)]
        noise = np.random.normal(0, 0.5, 7)
        return {
            "temp_max": [p + n for p, n in zip(preds, noise)],
            "temp_min": [p - 8 + n for p, n in zip(preds, noise)],
            "confidence_lower": [p - 2 for p in preds],
            "confidence_upper": [p + 2 for p in preds],
        }
