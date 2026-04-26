"""
Full ML Training Pipeline
Run: python -m app.ml.train_pipeline
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import mlflow
import mlflow.sklearn
import logging
import os
import sys

from app.ml.lstm_model import train_lstm, LSTMForecastService
from app.ml.xgboost_classifier import XGBoostClassifier
from app.ml.severity_model import SeverityScorer
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_synthetic_data(n_days: int = 3650, seed: int = 42) -> pd.DataFrame:
    """
    Generate realistic synthetic weather data for India (2014-2024).
    In production, replace this with real IMD/ERA5 data.
    """
    np.random.seed(seed)
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq="D")

    # Seasonal temperature pattern (Indian climate)
    day_of_year = np.array([d.timetuple().tm_yday for d in dates])
    seasonal_temp = 30 + 12 * np.sin(2 * np.pi * (day_of_year - 90) / 365)
    temp_trend = np.linspace(0, 1.5, n_days)  # 1.5°C warming over 10 years

    temp_max = seasonal_temp + temp_trend + np.random.normal(0, 2.5, n_days)
    temp_min = temp_max - 8 - np.abs(np.random.normal(0, 1.5, n_days))
    humidity = np.clip(
        60 - 20 * np.sin(2 * np.pi * (day_of_year - 180) / 365) + np.random.normal(0, 8, n_days),
        15, 95,
    )
    wind_speed = np.abs(np.random.normal(12, 5, n_days))
    pressure = 1010 + np.random.normal(0, 5, n_days)

    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "district": "Vijayawada",
        "state": "Andhra Pradesh",
        "temp_max": np.round(temp_max, 1),
        "temp_min": np.round(temp_min, 1),
        "humidity": np.round(humidity, 1),
        "wind_speed": np.round(wind_speed, 1),
        "pressure": np.round(pressure, 1),
        "uhi_score": np.round(np.random.uniform(0.3, 0.7, n_days), 2),
    })

    # Heat index
    T, RH = df["temp_max"], df["humidity"]
    df["heat_index"] = np.round(
        -8.78 + 1.61 * T + 2.34 * RH - 0.146 * T * RH
        - 0.0123 * T**2 - 0.0164 * RH**2, 1
    )

    return df


def compute_normals(df: pd.DataFrame) -> pd.DataFrame:
    """Compute 30-year climatological normals."""
    df = df.copy()
    df["day_of_year"] = pd.to_datetime(df["date"]).dt.dayofyear
    normals = df.groupby("day_of_year")["temp_max"].mean().reset_index()
    normals.columns = ["day_of_year", "normal_temp_max"]
    return normals


def train_all_models():
    """End-to-end training pipeline with MLflow tracking."""
    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(settings.MLFLOW_EXPERIMENT_NAME)

    logger.info("=" * 60)
    logger.info("🌡️  HEATWAVE PREDICTION — ML TRAINING PIPELINE")
    logger.info("=" * 60)

    # 1. Generate / load data
    logger.info("📊 Preparing training data...")
    full_df = generate_synthetic_data(n_days=3650)
    normals = compute_normals(full_df)

    split_idx = int(len(full_df) * 0.8)
    train_df = full_df.iloc[:split_idx].copy()
    val_df = full_df.iloc[split_idx:].copy()

    os.makedirs(settings.MODEL_DIR, exist_ok=True)

    with mlflow.start_run(run_name="full_ensemble_training"):
        mlflow.log_param("train_samples", len(train_df))
        mlflow.log_param("val_samples", len(val_df))
        mlflow.log_param("heatwave_threshold_temp", settings.HEATWAVE_THRESHOLD_TEMP)
        mlflow.log_param("forecast_days", settings.FORECAST_DAYS)

        # 2. Train LSTM
        logger.info("\n🧠 [1/3] Training LSTM Temperature Forecaster...")
        lstm_service = train_lstm(
            train_df=train_df,
            val_df=val_df,
            epochs=30,
            save_path=settings.LSTM_MODEL_PATH,
        )
        mlflow.log_artifact(settings.LSTM_MODEL_PATH, "models")
        logger.info("✅ LSTM training complete")

        # 3. Train XGBoost
        logger.info("\n🤖 [2/3] Training XGBoost Onset Classifier...")
        xgb_clf = XGBoostClassifier()
        xgb_metrics = xgb_clf.train(train_df, val_df, normals)
        xgb_clf.save(settings.XGBOOST_MODEL_PATH)
        mlflow.log_metrics({
            "xgb_val_f1": xgb_metrics.get("val_f1", 0),
            "xgb_val_auc": xgb_metrics.get("val_auc", 0),
        })
        mlflow.log_artifact(settings.XGBOOST_MODEL_PATH, "models")
        logger.info(f"✅ XGBoost training complete — {xgb_metrics}")

        # 4. Train Random Forest
        logger.info("\n🌲 [3/3] Training Random Forest Severity Scorer...")
        rf_scorer = SeverityScorer()
        rf_metrics = rf_scorer.train(train_df)
        rf_scorer.save(settings.RF_MODEL_PATH)
        mlflow.log_artifact(settings.RF_MODEL_PATH, "models")
        logger.info("✅ Random Forest training complete")

        # 5. Log summary
        mlflow.log_param("training_completed_at", datetime.now().isoformat())
        logger.info("\n" + "=" * 60)
        logger.info("🎉 ALL MODELS TRAINED SUCCESSFULLY")
        logger.info(f"   LSTM    → {settings.LSTM_MODEL_PATH}")
        logger.info(f"   XGBoost → {settings.XGBOOST_MODEL_PATH}")
        logger.info(f"   RF      → {settings.RF_MODEL_PATH}")
        logger.info("=" * 60)

    return {"status": "success", "models_trained": ["lstm", "xgboost", "random_forest"]}


if __name__ == "__main__":
    train_all_models()
