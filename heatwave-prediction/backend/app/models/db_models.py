"""Database models for heatwave prediction system."""

from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class WeatherObservation(Base):
    """Raw weather observations from API/sensors."""
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True, index=True)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    temp_max = Column(Float)          # °C
    temp_min = Column(Float)          # °C
    temp_mean = Column(Float)         # °C
    humidity = Column(Float)          # %
    wind_speed = Column(Float)        # km/h
    wind_direction = Column(Float)    # degrees
    pressure = Column(Float)          # hPa
    heat_index = Column(Float)        # computed
    uhi_score = Column(Float)         # urban heat island score
    source = Column(String(50))       # openweather / imd / sensor
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class HeatwavePrediction(Base):
    """ML model predictions for heatwave events."""
    __tablename__ = "heatwave_predictions"

    id = Column(Integer, primary_key=True, index=True)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    prediction_date = Column(DateTime(timezone=True), nullable=False, index=True)
    target_date = Column(DateTime(timezone=True), nullable=False)
    forecast_day = Column(Integer)    # 1-7

    # LSTM output
    predicted_temp_max = Column(Float)
    predicted_temp_min = Column(Float)
    temp_confidence_lower = Column(Float)
    temp_confidence_upper = Column(Float)

    # XGBoost output
    heatwave_probability = Column(Float)
    is_heatwave = Column(Boolean)

    # Random Forest output
    severity = Column(String(20))     # mild/moderate/severe/extreme
    severity_score = Column(Float)    # 0-1

    # Ensemble
    ensemble_confidence = Column(Float)
    alert_triggered = Column(Boolean, default=False)

    # SHAP
    shap_values = Column(JSON)        # top-5 feature contributions
    feature_names = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    alerts = relationship("AlertLog", back_populates="prediction")


class AlertLog(Base):
    """Log of all alerts sent."""
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("heatwave_predictions.id"))
    alert_type = Column(String(20))   # sms / email / push
    recipient = Column(String(255))
    message = Column(Text)
    status = Column(String(20))       # sent / failed / pending
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    prediction = relationship("HeatwavePrediction", back_populates="alerts")


class DistrictProfile(Base):
    """Demographic and geographic profile per district."""
    __tablename__ = "district_profiles"

    id = Column(Integer, primary_key=True, index=True)
    district = Column(String(100), nullable=False, unique=True)
    state = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    population = Column(Integer)
    elderly_population_pct = Column(Float)   # % aged 65+
    children_population_pct = Column(Float)  # % aged < 5
    green_cover_pct = Column(Float)          # % green area
    water_body_pct = Column(Float)
    urban_area_pct = Column(Float)
    hospital_count = Column(Integer)
    cooling_centres = Column(JSON)           # list of locations
    health_officer_phone = Column(String(20))
    health_officer_email = Column(String(255))


class ModelVersion(Base):
    """Track deployed model versions."""
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50))
    version = Column(String(20))
    mlflow_run_id = Column(String(100))
    accuracy = Column(Float)
    f1_score = Column(Float)
    rmse = Column(Float)
    deployed_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    metrics = Column(JSON)
