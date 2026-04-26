"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Heatwave Prediction System"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://heatwave:heatwave123@localhost:5432/heatwave_db"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_NAME: str = "heatwave_prediction"

    # Weather APIs
    OPENWEATHER_API_KEY: str = ""
    NASA_EARTHDATA_TOKEN: str = ""

    # Alerts
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    SENDGRID_API_KEY: str = ""
    ALERT_EMAIL_FROM: str = "alerts@heatwave-system.com"
    FIREBASE_SERVER_KEY: str = ""

    # Heatwave thresholds (IMD standard)
    HEATWAVE_THRESHOLD_TEMP: float = 40.0       # °C
    HEATWAVE_DEPARTURE_THRESHOLD: float = 4.5   # °C above normal
    ALERT_CONFIDENCE_THRESHOLD: float = 0.70    # 70% confidence
    FORECAST_DAYS: int = 7

    # Model paths
    MODEL_DIR: str = "/app/models"
    LSTM_MODEL_PATH: str = "/app/models/lstm_forecaster.pt"
    XGBOOST_MODEL_PATH: str = "/app/models/xgboost_classifier.json"
    RF_MODEL_PATH: str = "/app/models/rf_severity.pkl"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
