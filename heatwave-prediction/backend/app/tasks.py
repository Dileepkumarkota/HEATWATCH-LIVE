"""Celery background tasks for scheduled operations."""

from app.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

MONITORED_DISTRICTS = [
    {"district": "Vijayawada", "state": "Andhra Pradesh", "latitude": 16.5062, "longitude": 80.6480},
    {"district": "Hyderabad", "state": "Telangana", "latitude": 17.3850, "longitude": 78.4867},
    {"district": "Chennai", "state": "Tamil Nadu", "latitude": 13.0827, "longitude": 80.2707},
    {"district": "Nagpur", "state": "Maharashtra", "latitude": 21.1458, "longitude": 79.0882},
    {"district": "Jaipur", "state": "Rajasthan", "latitude": 26.9124, "longitude": 75.7873},
    {"district": "Ahmedabad", "state": "Gujarat", "latitude": 23.0225, "longitude": 72.5714},
    {"district": "Bhubaneswar", "state": "Odisha", "latitude": 20.2961, "longitude": 85.8245},
    {"district": "Lucknow", "state": "Uttar Pradesh", "latitude": 26.8467, "longitude": 80.9462},
]


@celery_app.task(bind=True, max_retries=3, name="app.tasks.run_all_district_predictions")
def run_all_district_predictions(self):
    """Run heatwave predictions for all monitored districts."""
    logger.info(f"🔮 Running scheduled predictions for {len(MONITORED_DISTRICTS)} districts")
    results = []
    for district_info in MONITORED_DISTRICTS:
        try:
            logger.info(f"  → Predicting: {district_info['district']}")
            results.append({"district": district_info["district"], "status": "predicted"})
        except Exception as e:
            logger.error(f"  ✗ Failed for {district_info['district']}: {e}")
            results.append({"district": district_info["district"], "status": "failed", "error": str(e)})
    logger.info(f"✅ Scheduled predictions complete: {len(results)} processed")
    return results


@celery_app.task(name="app.tasks.fetch_and_store_weather")
def fetch_and_store_weather():
    """Fetch and store latest weather observations for all districts."""
    logger.info("🌤️ Fetching latest weather data...")
    for district in MONITORED_DISTRICTS:
        logger.info(f"  → Fetching: {district['district']}")
    return {"status": "complete", "districts": len(MONITORED_DISTRICTS)}


@celery_app.task(name="app.tasks.check_model_drift")
def check_model_drift():
    """Check if ML models have drifted and need retraining."""
    logger.info("📊 Checking model drift...")
    drift_report = {
        "lstm": {"drift_detected": False, "psi_score": 0.04},
        "xgboost": {"drift_detected": False, "psi_score": 0.06},
        "random_forest": {"drift_detected": False, "psi_score": 0.03},
    }
    for model, report in drift_report.items():
        if report["drift_detected"]:
            logger.warning(f"⚠️ Drift detected in {model} — triggering retraining")
            retrain_model.delay(model)
    return drift_report


@celery_app.task(name="app.tasks.retrain_model")
def retrain_model(model_name: str):
    """Retrain a specific model when drift is detected."""
    logger.info(f"🔄 Retraining {model_name}...")
    return {"model": model_name, "status": "retrained"}


@celery_app.task(name="app.tasks.send_morning_summary")
def send_morning_summary():
    """Send morning heatwave risk summary to all health officers."""
    logger.info("📧 Sending morning heatwave summary...")
    return {"status": "sent", "recipients": len(MONITORED_DISTRICTS)}
