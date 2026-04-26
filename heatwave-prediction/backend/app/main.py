"""
Heatwave Prediction System — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.routes import predictions, alerts, health, websocket, data, explain
from app.core.config import settings
from app.core.database import engine, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🌡️ Starting Heatwave Prediction System...")
    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database tables ready")
    yield
    logger.info("🛑 Shutting down...")


app = FastAPI(
    title="Heatwave Prediction System API",
    description="""
    ## Advanced ML-powered Heatwave Early Warning System
    
    Predicts heatwaves 7 days in advance using an ensemble of:
    - **LSTM** — Temperature sequence forecasting
    - **XGBoost** — Heatwave onset classification  
    - **Random Forest** — Severity scoring
    - **SHAP** — Explainable AI for every prediction
    
    Automatically sends alerts to civic authorities when confidence > 70%.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ─────────────────────────────────────────────────
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(alerts.router, prefix="/api/v1", tags=["Alerts"])
app.include_router(explain.router, prefix="/api/v1", tags=["Explainability"])
app.include_router(data.router, prefix="/api/v1", tags=["Data"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "system": "Heatwave Prediction System",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "features": [
            "7-day heatwave forecast",
            "LSTM + XGBoost + Random Forest ensemble",
            "SHAP explainability",
            "Health risk mapping",
            "Automated alerts (SMS/Email/Push)",
            "Real-time WebSocket updates",
            "Model drift monitoring",
        ],
    }
