"""
XGBoost Heatwave Onset Classifier
Classifies whether a heatwave will begin in the next N days.
Uses IMD definition: Tmax >= 40°C AND departure >= 4.5°C above normal.
"""

import xgboost as xgb
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import classification_report, roc_auc_score, f1_score
from typing import Dict, List, Tuple, Any
import joblib
import logging
import os

logger = logging.getLogger(__name__)

CLASSIFIER_FEATURES = [
    # Temperature features
    "temp_max", "temp_max_anomaly", "temp_max_lag1", "temp_max_lag3", "temp_max_lag7",
    "temp_max_rolling3", "temp_max_rolling7", "temp_max_rolling14",
    "temp_min", "temp_range",
    # Humidity features
    "humidity", "humidity_lag1", "humidity_rolling7", "humidity_anomaly",
    # Wind
    "wind_speed", "wind_speed_rolling7",
    # Pressure
    "pressure", "pressure_change_24h",
    # Heat index & derived
    "heat_index", "heat_index_lag1", "heat_index_rolling7",
    "wet_bulb_temp",
    # Urban heat island
    "uhi_score",
    # Time features
    "month", "day_of_year", "month_sin", "month_cos", "is_pre_monsoon",
    # Consecutive days
    "consecutive_hot_days", "consecutive_dry_days",
]


class XGBoostClassifier:
    """Heatwave onset classifier using XGBoost with SHAP explainability."""

    def __init__(self, model_path: str = None):
        self.model = None
        self.explainer = None
        self.feature_names = CLASSIFIER_FEATURES
        self.thresholds = {
            "temp": 40.0,     # IMD: Tmax >= 40°C for plains
            "departure": 4.5, # IMD: >= 4.5°C above normal
        }

        if model_path and os.path.exists(model_path):
            self.load(model_path)
        else:
            self._init_model()
            logger.warning("No saved XGBoost model found — using fresh model")

    def _init_model(self):
        self.model = xgb.XGBClassifier(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            scale_pos_weight=3,    # handle class imbalance (heatwaves are rare)
            objective="binary:logistic",
            eval_metric=["logloss", "auc"],
            use_label_encoder=False,
            random_state=42,
            n_jobs=-1,
        )

    def engineer_features(self, df: pd.DataFrame, normals_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Engineer all features for the classifier.
        normals_df: climatological normals (30-year average per DOY) for anomaly calc.
        """
        df = df.copy().sort_values("date")
        dt = pd.to_datetime(df["date"])

        # Basic lags
        df["temp_max_lag1"] = df["temp_max"].shift(1)
        df["temp_max_lag3"] = df["temp_max"].shift(3)
        df["temp_max_lag7"] = df["temp_max"].shift(7)
        df["humidity_lag1"] = df["humidity"].shift(1)
        df["heat_index_lag1"] = df["heat_index"].shift(1)

        # Rolling means
        df["temp_max_rolling3"]  = df["temp_max"].rolling(3).mean()
        df["temp_max_rolling7"]  = df["temp_max"].rolling(7).mean()
        df["temp_max_rolling14"] = df["temp_max"].rolling(14).mean()
        df["humidity_rolling7"]  = df["humidity"].rolling(7).mean()
        df["heat_index_rolling7"] = df["heat_index"].rolling(7).mean()
        df["wind_speed_rolling7"] = df["wind_speed"].rolling(7).mean()

        # Temperature range and derived
        df["temp_range"] = df["temp_max"] - df["temp_min"]
        df["pressure_change_24h"] = df["pressure"].diff(1)

        # Anomaly from climatological normal
        df["day_of_year"] = dt.dt.dayofyear
        if normals_df is not None:
            df = df.merge(normals_df[["day_of_year", "normal_temp_max"]], on="day_of_year", how="left")
            df["temp_max_anomaly"] = df["temp_max"] - df["normal_temp_max"]
        else:
            df["temp_max_anomaly"] = df["temp_max"] - df["temp_max_rolling30"] if "temp_max_rolling30" in df.columns else 0
            df["humidity_anomaly"] = df["humidity"] - df["humidity"].mean()

        # Wet bulb temperature approximation
        T = df["temp_max"]
        RH = df["humidity"]
        df["wet_bulb_temp"] = T * np.arctan(0.151977 * (RH + 8.313659) ** 0.5) + \
                               np.arctan(T + RH) - \
                               np.arctan(RH - 1.676331) + \
                               0.00391838 * RH ** 1.5 * np.arctan(0.023101 * RH) - 4.686035

        # Time features
        df["month"] = dt.dt.month
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
        df["is_pre_monsoon"] = df["month"].isin([3, 4, 5, 6]).astype(int)

        # Consecutive hot/dry days
        df["is_hot_day"] = (df["temp_max"] >= 38).astype(int)
        df["is_dry_day"] = (df["humidity"] < 30).astype(int)
        df["consecutive_hot_days"] = df["is_hot_day"].groupby(
            (df["is_hot_day"] != df["is_hot_day"].shift()).cumsum()
        ).cumsum()
        df["consecutive_dry_days"] = df["is_dry_day"].groupby(
            (df["is_dry_day"] != df["is_dry_day"].shift()).cumsum()
        ).cumsum()

        if "uhi_score" not in df.columns:
            df["uhi_score"] = 0.0

        return df.dropna(subset=["temp_max_lag7"])

    def create_labels(self, df: pd.DataFrame) -> pd.Series:
        """Create binary heatwave label using IMD definition."""
        labels = (
            (df["temp_max"] >= self.thresholds["temp"]) &
            (df["temp_max_anomaly"] >= self.thresholds["departure"])
        ).astype(int)
        return labels

    def train(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None,
              normals_df: pd.DataFrame = None) -> Dict[str, float]:
        """Train XGBoost classifier with cross-validation."""
        logger.info("🤖 Training XGBoost classifier...")
        X_train = self.engineer_features(train_df, normals_df)[self.feature_names]
        y_train = self.create_labels(self.engineer_features(train_df, normals_df))

        eval_set = []
        if val_df is not None:
            X_val = self.engineer_features(val_df, normals_df)[self.feature_names]
            y_val = self.create_labels(self.engineer_features(val_df, normals_df))
            eval_set = [(X_val, y_val)]

        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=50,
        )

        # Initialize SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)

        # Metrics
        y_pred = self.model.predict(X_train)
        y_prob = self.model.predict_proba(X_train)[:, 1]
        metrics = {
            "train_f1": f1_score(y_train, y_pred),
            "train_auc": roc_auc_score(y_train, y_prob),
        }
        if val_df is not None:
            v_pred = self.model.predict(X_val)
            v_prob = self.model.predict_proba(X_val)[:, 1]
            metrics["val_f1"] = f1_score(y_val, v_pred)
            metrics["val_auc"] = roc_auc_score(y_val, v_prob)

        logger.info(f"✅ XGBoost trained — {metrics}")
        return metrics

    def predict(self, df: pd.DataFrame, normals_df: pd.DataFrame = None) -> Dict[str, Any]:
        """Predict heatwave probability and get SHAP explanations."""
        df_feat = self.engineer_features(df, normals_df)
        X = df_feat[self.feature_names].iloc[[-1]]  # latest row

        proba = self.model.predict_proba(X)[0, 1] if self.model else 0.5
        is_hw = bool(proba >= 0.5)

        # SHAP values
        shap_values = None
        top_features = []
        if self.explainer:
            sv = self.explainer.shap_values(X)
            sv_arr = sv[0] if isinstance(sv, list) else sv[0]
            shap_pairs = sorted(
                zip(self.feature_names, sv_arr, X.values[0]),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:5]
            top_features = [
                {
                    "feature": f,
                    "shap_value": float(sv),
                    "value": float(val),
                    "direction": "increases_risk" if sv > 0 else "decreases_risk",
                }
                for f, sv, val in shap_pairs
            ]

        return {
            "heatwave_probability": float(proba),
            "is_heatwave": is_hw,
            "top_shap_features": top_features,
        }

    def save(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save_model(path)
        if self.explainer:
            joblib.dump(self.explainer, path.replace(".json", "_explainer.pkl"))
        logger.info(f"💾 XGBoost model saved to {path}")

    def load(self, path: str):
        self._init_model()
        self.model.load_model(path)
        explainer_path = path.replace(".json", "_explainer.pkl")
        if os.path.exists(explainer_path):
            self.explainer = joblib.load(explainer_path)
        else:
            self.explainer = shap.TreeExplainer(self.model)
        logger.info(f"✅ XGBoost model loaded from {path}")
