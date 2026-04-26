"""
Random Forest Severity Scorer
Scores heatwave severity: none / mild / moderate / severe / extreme
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
from typing import Dict, Any
import joblib
import logging
import os

logger = logging.getLogger(__name__)

SEVERITY_FEATURES = [
    "predicted_temp_max", "temp_max_anomaly", "heat_index",
    "humidity", "consecutive_hot_days", "uhi_score",
    "elderly_population_pct", "urban_area_pct", "green_cover_pct",
    "month", "duration_days",
]

SEVERITY_LABELS = ["none", "mild", "moderate", "severe", "extreme"]

# IMD severity thresholds
SEVERITY_RULES = {
    "extreme": {"temp": 47, "departure": 6.5},
    "severe": {"temp": 44, "departure": 6.5},
    "moderate": {"temp": 42, "departure": 5.5},
    "mild": {"temp": 40, "departure": 4.5},
    "none": {"temp": 0, "departure": 0},
}


class SeverityScorer:
    """Random Forest model to classify heatwave severity."""

    def __init__(self, model_path: str = None):
        self.model = RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_split=10,
            min_samples_leaf=5,
            class_weight="balanced",
            n_jobs=-1,
            random_state=42,
        )
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(SEVERITY_LABELS)
        self.feature_names = SEVERITY_FEATURES
        self._trained = False

        if model_path and os.path.exists(model_path):
            self.load(model_path)

    def rule_based_severity(self, temp_max: float, anomaly: float, duration: int = 1) -> str:
        """
        Fallback rule-based severity using IMD standards.
        Used when ML model is not yet trained.
        """
        if temp_max >= SEVERITY_RULES["extreme"]["temp"] or anomaly >= SEVERITY_RULES["extreme"]["departure"]:
            return "extreme"
        elif temp_max >= SEVERITY_RULES["severe"]["temp"] or anomaly >= SEVERITY_RULES["severe"]["departure"]:
            return "severe"
        elif temp_max >= SEVERITY_RULES["moderate"]["temp"] or anomaly >= SEVERITY_RULES["moderate"]["departure"]:
            if duration >= 3:
                return "severe"
            return "moderate"
        elif temp_max >= SEVERITY_RULES["mild"]["temp"] and anomaly >= SEVERITY_RULES["mild"]["departure"]:
            return "mild"
        return "none"

    def severity_score(self, severity_label: str) -> float:
        """Convert severity label to 0-1 score."""
        mapping = {"none": 0.0, "mild": 0.25, "moderate": 0.5, "severe": 0.75, "extreme": 1.0}
        return mapping.get(severity_label, 0.0)

    def create_labels(self, df: pd.DataFrame) -> pd.Series:
        """Create severity labels from weather data."""
        def classify(row):
            return self.rule_based_severity(
                row.get("temp_max", 0),
                row.get("temp_max_anomaly", 0),
                int(row.get("consecutive_hot_days", 1))
            )
        return df.apply(classify, axis=1)

    def train(self, df: pd.DataFrame, district_profiles: pd.DataFrame = None) -> Dict[str, Any]:
        """Train the severity scoring model."""
        logger.info("🌲 Training Random Forest severity scorer...")

        if district_profiles is not None:
            df = df.merge(district_profiles[["district", "elderly_population_pct",
                                              "urban_area_pct", "green_cover_pct"]],
                          on="district", how="left")
        else:
            df["elderly_population_pct"] = 0.12
            df["urban_area_pct"] = 0.45
            df["green_cover_pct"] = 0.20

        if "duration_days" not in df.columns:
            df["duration_days"] = df.get("consecutive_hot_days", 1)
        if "predicted_temp_max" not in df.columns:
            df["predicted_temp_max"] = df["temp_max"]

        X = df[self.feature_names].fillna(0)
        y_labels = self.create_labels(df)
        y = self.label_encoder.transform(y_labels)

        self.model.fit(X, y)
        self._trained = True

        y_pred = self.label_encoder.inverse_transform(self.model.predict(X))
        report = classification_report(y_labels, y_pred, output_dict=True)
        logger.info(f"✅ Severity model trained — accuracy: {report.get('accuracy', 0):.3f}")
        return report

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Predict severity from feature dict."""
        temp_max = features.get("predicted_temp_max", features.get("temp_max", 35))
        anomaly = features.get("temp_max_anomaly", 0)
        duration = features.get("consecutive_hot_days", 1)

        if not self._trained:
            label = self.rule_based_severity(temp_max, anomaly, int(duration))
            score = self.severity_score(label)
            return {"severity": label, "severity_score": score, "method": "rule_based"}

        X = pd.DataFrame([{f: features.get(f, 0) for f in self.feature_names}])
        proba = self.model.predict_proba(X)[0]
        pred_idx = np.argmax(proba)
        label = self.label_encoder.inverse_transform([pred_idx])[0]

        return {
            "severity": label,
            "severity_score": self.severity_score(label),
            "probabilities": {
                lbl: float(p)
                for lbl, p in zip(self.label_encoder.classes_, proba)
            },
            "method": "ml",
        }

    def get_recommended_actions(self, severity: str, district_data: Dict = None) -> list:
        """Return recommended actions based on severity level."""
        base_actions = {
            "none": ["Monitor weather forecasts", "Stay hydrated"],
            "mild": [
                "Issue public health advisory",
                "Ensure adequate water supply",
                "Open cooling centres",
                "Monitor vulnerable populations",
            ],
            "moderate": [
                "Activate district heat action plan",
                "Alert hospitals to prepare for heat-related illness",
                "SMS advisory to registered citizens",
                "Restrict outdoor labour 12PM-3PM",
                "Deploy mobile water tankers",
            ],
            "severe": [
                "IMMEDIATE: Alert district collector and health officer",
                "Deploy emergency medical teams",
                "Mandatory cooling centre activation",
                "School and outdoor activity suspension",
                "24/7 heat helpline activation",
                "Prioritise elderly and child welfare checks",
            ],
            "extreme": [
                "🚨 DECLARE HEAT EMERGENCY",
                "Evacuate vulnerable populations to cooling centres",
                "Deploy NDRF if mortality risk is high",
                "Maximum media alert dissemination",
                "Hospital emergency protocols activated",
                "Complete outdoor activity ban 10AM-6PM",
            ],
        }
        return base_actions.get(severity, [])

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"model": self.model, "label_encoder": self.label_encoder}, path)
        logger.info(f"💾 Severity model saved to {path}")

    def load(self, path: str):
        data = joblib.load(path)
        self.model = data["model"]
        self.label_encoder = data["label_encoder"]
        self._trained = True
        logger.info(f"✅ Severity model loaded from {path}")
