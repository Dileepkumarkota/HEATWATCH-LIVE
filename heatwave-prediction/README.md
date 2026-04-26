# 🌡️ Advanced Heatwave Prediction System

A production-grade ML + Full Stack system that predicts heatwaves 7 days in advance, identifies vulnerable populations, and sends automated early warnings.

> **This is NOT a weather app.** Weather apps show current conditions. This system uses a 4-model ML ensemble trained on historical climate data to predict future heatwaves, quantifies health risk by district, and triggers automated civic alerts — with SHAP-based explainability.

---

## 🏗️ Architecture

```
Data Sources → Kafka Pipeline → Feature Engineering → ML Ensemble → FastAPI → React Frontend
               (OpenWeather,     (Heat index, UHI,    (LSTM + XGBoost  (REST/WS)   (Map, Dashboard,
                NASA MODIS,       lag features,         + RF + SHAP)                 Alerts, XAI)
                IoT sensors)      Redis cache)
```

## 🚀 Features

| Feature | Description |
|---|---|
| **7-day heatwave forecast** | LSTM neural network for temperature sequence prediction |
| **Onset classification** | XGBoost classifies if/when a heatwave will begin |
| **Severity scoring** | Random Forest scores mild / moderate / extreme |
| **Spatial propagation** | Graph Neural Network models cross-district heat spread |
| **Explainability (XAI)** | SHAP values show why each prediction was made |
| **Health impact mapping** | Vulnerable population risk by district |
| **Automated alerts** | SMS (Twilio), Email (SendGrid), Push (Firebase) |
| **Model monitoring** | Drift detection with Evidently AI |
| **Interactive map** | Leaflet.js choropleth with risk zones |
| **Real-time updates** | WebSocket live dashboard |

## 🛠️ Tech Stack

### Backend
- **FastAPI** — REST + WebSocket API
- **Celery + Redis** — Async task queue
- **PostgreSQL** — Time-series weather data
- **MLflow** — Experiment tracking & model registry
- **Apache Kafka** — Real-time data streaming

### ML
- **PyTorch** — LSTM time-series model
- **XGBoost** — Heatwave onset classifier
- **scikit-learn** — Random Forest severity scorer
- **SHAP** — Model explainability
- **Pandas + NumPy** — Feature engineering

### Frontend
- **React 18** — UI framework
- **Tailwind CSS** — Styling
- **Leaflet.js** — Interactive maps
- **Chart.js / Recharts** — Data visualisation
- **Socket.io** — Real-time WebSocket

### DevOps
- **Docker + Docker Compose** — Containerisation
- **GitHub Actions** — CI/CD pipeline
- **Prometheus + Grafana** — Monitoring

---

## 📦 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+
- Node.js 18+

### 1. Clone & Configure
```bash
git clone <repo-url>
cd heatwave-prediction
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Start with Docker
```bash
docker-compose up --build
```

### 3. Train ML Models
```bash
docker-compose exec backend python -m app.ml.train_pipeline
```

### 4. Access
- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **MLflow UI:** http://localhost:5000
- **Grafana:** http://localhost:3001

---

## 📁 Project Structure

```
heatwave-prediction/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── ml/           # ML models & training
│   │   ├── services/     # Business logic
│   │   └── models/       # DB models
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page views
│   │   ├── hooks/        # Custom hooks
│   │   └── utils/        # Helpers
│   ├── Dockerfile
│   └── package.json
├── notebooks/            # Jupyter EDA notebooks
├── data/                 # Sample datasets
├── .github/workflows/    # CI/CD
└── docker-compose.yml
```

---

## 🧠 ML Models Detail

### 1. LSTM Temperature Forecaster
- Input: 30-day sliding window of temperature, humidity, wind, pressure
- Output: 7-day temperature sequence with confidence intervals
- Architecture: 2-layer LSTM → Dense → Output

### 2. XGBoost Onset Classifier
- Input: 50+ engineered features (heat index, UHI score, humidity anomaly, etc.)
- Output: Binary (heatwave / no heatwave) + probability
- Threshold: IMD definition (Tmax ≥ 40°C AND departure ≥ 4.5°C)

### 3. Random Forest Severity Scorer
- Input: Predicted temperatures + population density + green cover
- Output: mild / moderate / severe / extreme

### 4. SHAP Explainability
- Every prediction comes with top-5 contributing features
- SHAP waterfall plots rendered in the frontend

---

## 🔔 Alert System

When a heatwave is predicted 48h ahead with confidence > 70%:
1. SMS alert sent to district health officers via Twilio
2. Email report to municipal corporation
3. Push notification to registered public users
4. Dashboard auto-highlights affected zones

---

## 📊 Faculty Talking Points

> *"Weather apps show current conditions. Our system uses an ensemble of 4 ML models — LSTM, XGBoost, Random Forest, and a Graph Neural Network — trained on 30+ years of IMD data to predict heatwaves 7 days in advance. We add SHAP-based explainability, health risk mapping for vulnerable populations by district, and automated early warning alerts to civic authorities. This is an end-to-end production MLOps system."*

---

## 📄 License
MIT
