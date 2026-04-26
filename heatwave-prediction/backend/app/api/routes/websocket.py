"""WebSocket router for real-time heatwave updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json
import numpy as np
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

connected_clients: list[WebSocket] = []


@router.websocket("/heatwave")
async def heatwave_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time heatwave dashboard updates.
    Pushes live temperature readings and alert status every 5 seconds.
    """
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(connected_clients)}")

    try:
        while True:
            # Push live simulated sensor data
            data = {
                "type": "live_update",
                "timestamp": datetime.now().isoformat(),
                "districts": [
                    {
                        "district": "Vijayawada",
                        "current_temp": round(38 + np.random.normal(0, 0.3), 1),
                        "humidity": round(45 + np.random.normal(0, 1), 1),
                        "heat_index": round(42 + np.random.normal(0, 0.4), 1),
                        "alert_status": "warning",
                    },
                    {
                        "district": "Hyderabad",
                        "current_temp": round(40 + np.random.normal(0, 0.3), 1),
                        "humidity": round(38 + np.random.normal(0, 1), 1),
                        "heat_index": round(44 + np.random.normal(0, 0.4), 1),
                        "alert_status": "severe",
                    },
                ],
                "active_alerts": np.random.randint(0, 3),
                "districts_monitored": 8,
            }
            await websocket.send_text(json.dumps(data))
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(connected_clients)}")


async def broadcast_alert(alert_data: dict):
    """Broadcast a heatwave alert to all connected WebSocket clients."""
    message = json.dumps({"type": "alert", **alert_data})
    disconnected = []
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            disconnected.append(client)
    for c in disconnected:
        connected_clients.remove(c)
