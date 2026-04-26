"""
LSTM Temperature Forecasting Model
Predicts 7-day temperature sequences with confidence intervals.
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, Dict, Any
import logging
import joblib
import os

logger = logging.getLogger(__name__)

SEQUENCE_LENGTH = 30   # 30-day input window
FORECAST_DAYS = 7
FEATURES = [
    "temp_max", "temp_min", "humidity", "wind_speed",
    "pressure", "heat_index", "uhi_score",
    "temp_max_lag1", "temp_max_lag7", "humidity_lag1",
    "temp_max_rolling7", "temp_max_rolling30",
    "humidity_rolling7", "month_sin", "month_cos",
]


class LSTMForecaster(nn.Module):
    """
    2-layer bidirectional LSTM for multi-step temperature forecasting.
    
    Architecture:
        Input(seq=30, features=15) → LSTM(256) → LSTM(128) → Dense(64) → Output(7×2)
    """

    def __init__(
        self,
        input_size: int = len(FEATURES),
        hidden_size: int = 256,
        num_layers: int = 2,
        output_size: int = FORECAST_DAYS * 2,  # temp_max + temp_min per day
        dropout: float = 0.3,
    ):
        super(LSTMForecaster, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.forecast_days = FORECAST_DAYS

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
            bidirectional=False,
        )
        self.attention = nn.Linear(hidden_size, 1)
        self.fc1 = nn.Linear(hidden_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.output = nn.Linear(64, output_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # LSTM
        lstm_out, _ = self.lstm(x)              # (batch, seq, hidden)

        # Attention mechanism
        attn_weights = torch.softmax(self.attention(lstm_out), dim=1)
        context = (attn_weights * lstm_out).sum(dim=1)   # (batch, hidden)

        # Dense layers
        out = self.relu(self.fc1(context))
        out = self.dropout(out)
        out = self.relu(self.fc2(out))
        out = self.output(out)                  # (batch, 14) → 7 days × 2 temps

        return out.view(-1, self.forecast_days, 2)


class LSTMForecastService:
    """Service wrapper around LSTM model for inference."""

    def __init__(self, model_path: str = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = LSTMForecaster()
        self.scaler = MinMaxScaler()
        self.model_path = model_path
        self._loaded = False

        if model_path and os.path.exists(model_path):
            self.load(model_path)
        else:
            logger.warning("No saved LSTM model found — using untrained model (run training first)")

    def load(self, path: str):
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.scaler = checkpoint.get("scaler", self.scaler)
        self.model.eval()
        self._loaded = True
        logger.info(f"✅ LSTM model loaded from {path}")

    def save(self, path: str, extra: dict = None):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "scaler": self.scaler,
            **(extra or {}),
        }, path)
        logger.info(f"💾 LSTM model saved to {path}")

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create all input features from raw weather data."""
        df = df.copy().sort_values("date")

        # Lag features
        df["temp_max_lag1"] = df["temp_max"].shift(1)
        df["temp_max_lag7"] = df["temp_max"].shift(7)
        df["humidity_lag1"] = df["humidity"].shift(1)

        # Rolling statistics
        df["temp_max_rolling7"] = df["temp_max"].rolling(7).mean()
        df["temp_max_rolling30"] = df["temp_max"].rolling(30).mean()
        df["humidity_rolling7"] = df["humidity"].rolling(7).mean()

        # Cyclical time features
        months = pd.to_datetime(df["date"]).dt.month
        df["month_sin"] = np.sin(2 * np.pi * months / 12)
        df["month_cos"] = np.cos(2 * np.pi * months / 12)

        # Heat index (Steadman approximation)
        T = df["temp_max"]
        RH = df["humidity"]
        df["heat_index"] = (
            -8.78469475556
            + 1.61139411 * T
            + 2.33854883889 * RH
            - 0.14611605 * T * RH
            - 0.012308094 * T**2
            - 0.016424828 * RH**2
            + 0.002211732 * T**2 * RH
            + 0.00072546 * T * RH**2
            - 0.000003582 * T**2 * RH**2
        )

        if "uhi_score" not in df.columns:
            df["uhi_score"] = 0.0

        return df.dropna()

    def predict(self, recent_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run inference on 30 days of recent weather data.
        Returns 7-day forecast with confidence intervals.
        """
        df = self.engineer_features(recent_df)

        if len(df) < SEQUENCE_LENGTH:
            raise ValueError(f"Need at least {SEQUENCE_LENGTH} days of data, got {len(df)}")

        # Prepare input tensor
        feature_data = df[FEATURES].values[-SEQUENCE_LENGTH:]
        scaled = self.scaler.transform(feature_data) if self._loaded else feature_data
        x = torch.FloatTensor(scaled).unsqueeze(0).to(self.device)   # (1, 30, 15)

        with torch.no_grad():
            # Monte Carlo dropout for uncertainty (run 50 forward passes)
            self.model.train()  # enable dropout
            predictions = []
            for _ in range(50):
                pred = self.model(x).cpu().numpy()
                predictions.append(pred)
            self.model.eval()

        predictions = np.array(predictions)     # (50, 1, 7, 2)
        mean_pred = predictions.mean(axis=0)[0]   # (7, 2)
        std_pred = predictions.std(axis=0)[0]     # (7, 2)

        # Inverse transform if scaler was fitted
        result = {
            "temp_max": mean_pred[:, 0].tolist(),
            "temp_min": mean_pred[:, 1].tolist(),
            "temp_max_std": std_pred[:, 0].tolist(),
            "temp_min_std": std_pred[:, 1].tolist(),
            "confidence_lower": (mean_pred[:, 0] - 1.96 * std_pred[:, 0]).tolist(),
            "confidence_upper": (mean_pred[:, 0] + 1.96 * std_pred[:, 0]).tolist(),
        }
        return result


def train_lstm(train_df: pd.DataFrame, val_df: pd.DataFrame, epochs: int = 50, save_path: str = None):
    """Training loop for the LSTM model."""
    service = LSTMForecastService()
    service.engineer_features(train_df)

    # Fit scaler on training data
    feature_data = service.engineer_features(train_df)[FEATURES].values
    service.scaler.fit(feature_data)

    model = service.model.to(service.device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)
    criterion = nn.HuberLoss()

    best_val_loss = float("inf")

    for epoch in range(epochs):
        model.train()
        train_loss = _run_epoch(model, train_df, service, criterion, optimizer)
        val_loss = _run_epoch(model, val_df, service, criterion, optimizer=None)
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            if save_path:
                service.model = model
                service.save(save_path, {"epoch": epoch, "val_loss": val_loss})

        if epoch % 10 == 0:
            logger.info(f"Epoch {epoch}/{epochs} — Train: {train_loss:.4f}, Val: {val_loss:.4f}")

    return service


def _run_epoch(model, df, service, criterion, optimizer=None) -> float:
    """Run one epoch of training or validation."""
    df_feat = service.engineer_features(df)
    features = df_feat[FEATURES].values
    scaled = service.scaler.transform(features)

    losses = []
    for i in range(SEQUENCE_LENGTH, len(scaled) - FORECAST_DAYS):
        x = torch.FloatTensor(scaled[i - SEQUENCE_LENGTH:i]).unsqueeze(0)
        y_raw = df_feat[["temp_max", "temp_min"]].values[i:i + FORECAST_DAYS]
        y = torch.FloatTensor(y_raw).unsqueeze(0)

        if optimizer:
            optimizer.zero_grad()

        pred = model(x)
        loss = criterion(pred, y)

        if optimizer:
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        losses.append(loss.item())

    return np.mean(losses) if losses else 0.0
