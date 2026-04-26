"""Celery application for background tasks and scheduled jobs."""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    "heatwave",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Kolkata",
    enable_utc=True,
    beat_schedule={
        # Run predictions for all districts every 6 hours
        "predict-all-districts": {
            "task": "app.tasks.run_all_district_predictions",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        # Fetch fresh weather data every hour
        "fetch-weather-data": {
            "task": "app.tasks.fetch_and_store_weather",
            "schedule": crontab(minute=0),
        },
        # Check model drift daily at midnight
        "check-model-drift": {
            "task": "app.tasks.check_model_drift",
            "schedule": crontab(minute=0, hour=0),
        },
        # Send morning summary report at 7am
        "morning-summary": {
            "task": "app.tasks.send_morning_summary",
            "schedule": crontab(minute=0, hour=7),
        },
    },
)
