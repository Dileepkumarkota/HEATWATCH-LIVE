"""Backend API tests."""

import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Heatwave" in data["system"]
    assert len(data["features"]) > 0


@pytest.mark.asyncio
async def test_explain_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/explain/Vijayawada")
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Vijayawada"
    assert len(data["explanation"]) > 0


@pytest.mark.asyncio
async def test_districts_list():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/data/districts")
    assert response.status_code == 200
    assert len(response.json()["districts"]) >= 5


@pytest.mark.asyncio
async def test_model_metrics():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/data/model-metrics")
    assert response.status_code == 200
    models = response.json()["models"]
    assert len(models) == 3


def test_lstm_architecture():
    """Test LSTM model can forward pass."""
    import torch
    from app.ml.lstm_model import LSTMForecaster, FEATURES
    model = LSTMForecaster()
    x = torch.randn(2, 30, len(FEATURES))
    out = model(x)
    assert out.shape == (2, 7, 2)


def test_severity_rule_based():
    """Test severity scorer rule-based fallback."""
    from app.ml.severity_model import SeverityScorer
    scorer = SeverityScorer()
    assert scorer.rule_based_severity(47.0, 7.0) == "extreme"
    assert scorer.rule_based_severity(44.0, 6.5) == "severe"
    assert scorer.rule_based_severity(35.0, 2.0) == "none"


def test_feature_engineering():
    """Test XGBoost feature engineering."""
    import pandas as pd
    import numpy as np
    from app.ml.xgboost_classifier import XGBoostClassifier
    clf = XGBoostClassifier()
    dates = pd.date_range(end="2024-05-01", periods=60, freq="D")
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "temp_max": np.random.uniform(35, 45, 60),
        "temp_min": np.random.uniform(25, 35, 60),
        "humidity": np.random.uniform(20, 70, 60),
        "wind_speed": np.random.uniform(5, 25, 60),
        "pressure": np.random.uniform(1000, 1020, 60),
        "heat_index": np.random.uniform(38, 50, 60),
    })
    result = clf.engineer_features(df)
    assert "consecutive_hot_days" in result.columns
    assert "month_sin" in result.columns
    assert len(result) > 0


def test_ensemble_mock_prediction():
    """Test ensemble predictor with synthetic data."""
    import pandas as pd
    import numpy as np
    from app.ml.ensemble import EnsemblePredictor
    predictor = EnsemblePredictor()
    dates = pd.date_range(end="2024-05-01", periods=35, freq="D")
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "temp_max": np.random.uniform(38, 44, 35),
        "temp_min": np.random.uniform(28, 34, 35),
        "humidity": np.random.uniform(25, 55, 35),
        "wind_speed": np.random.uniform(8, 20, 35),
        "pressure": np.random.uniform(1005, 1015, 35),
        "heat_index": np.random.uniform(40, 50, 35),
        "uhi_score": np.random.uniform(0.4, 0.7, 35),
    })
    district_info = {
        "district": "TestDistrict", "state": "TestState",
        "population": 500000, "elderly_population_pct": 0.10,
        "children_population_pct": 0.18, "green_cover_pct": 0.20,
        "urban_area_pct": 0.55, "uhi_score": 0.50, "cooling_centres": [],
    }
    result = predictor.predict(df, district_info)
    assert "forecast" in result
    assert len(result["forecast"]) == 7
    assert "ensemble_confidence" in result
    assert 0 <= result["ensemble_confidence"] <= 1
