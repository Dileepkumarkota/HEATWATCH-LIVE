"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"


class DayForecast(BaseModel):
    date: str
    day: int
    predicted_temp_max: float
    predicted_temp_min: float
    confidence_lower: float
    confidence_upper: float
    heatwave_probability: float
    is_heatwave: bool
    severity: SeverityLevel
    severity_score: float


class SHAPFeature(BaseModel):
    feature: str
    value: float
    shap_value: float
    direction: str  # "increases_risk" | "decreases_risk"


class PredictionResponse(BaseModel):
    district: str
    state: str
    prediction_date: str
    forecast: List[DayForecast]
    ensemble_confidence: float
    alert_required: bool
    top_risk_factors: List[SHAPFeature]
    health_risk: Dict[str, Any]
    cooling_centres: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class PredictionRequest(BaseModel):
    district: str = Field(..., example="Vijayawada")
    state: str = Field(..., example="Andhra Pradesh")
    latitude: float = Field(..., example=16.5062)
    longitude: float = Field(..., example=80.6480)


class AlertRequest(BaseModel):
    district: str
    prediction_id: int
    alert_types: List[str] = ["sms", "email"]
    recipients: List[str]


class AlertResponse(BaseModel):
    alert_id: int
    status: str
    sent_to: List[str]
    message: str
    timestamp: str


class DistrictRiskSummary(BaseModel):
    district: str
    state: str
    latitude: float
    longitude: float
    current_severity: SeverityLevel
    max_predicted_temp: float
    heatwave_probability: float
    vulnerable_population: int
    risk_score: float  # 0-100


class HealthImpactResponse(BaseModel):
    district: str
    total_population: int
    vulnerable_population: int
    elderly_at_risk: int
    children_at_risk: int
    risk_level: str
    recommended_actions: List[str]
    nearest_cooling_centres: List[Dict[str, Any]]


class ModelMetrics(BaseModel):
    model_name: str
    version: str
    accuracy: float
    f1_score: float
    rmse: float
    last_trained: str
    drift_detected: bool
    drift_score: float


class WeatherDataPoint(BaseModel):
    district: str
    observed_at: str
    temp_max: float
    temp_min: float
    humidity: float
    wind_speed: float
    heat_index: float
    uhi_score: Optional[float] = None
