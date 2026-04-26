"""
Alert Service — SMS (Twilio), Email (SendGrid), Push (Firebase)
Sends automated early warning alerts to civic authorities.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertService:
    """Sends multi-channel alerts when heatwave confidence > threshold."""

    def __init__(self):
        self._twilio_client = None
        self._sendgrid_client = None
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients (graceful fallback if keys not set)."""
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                self._twilio_client = Client(
                    settings.TWILIO_ACCOUNT_SID,
                    settings.TWILIO_AUTH_TOKEN,
                )
                logger.info("✅ Twilio SMS client initialized")
            except ImportError:
                logger.warning("Twilio not installed")
        else:
            logger.info("ℹ️ Twilio not configured — SMS alerts disabled")

        if settings.SENDGRID_API_KEY:
            try:
                import sendgrid
                self._sendgrid_client = sendgrid.SendGridAPIClient(settings.SENDGRID_API_KEY)
                logger.info("✅ SendGrid email client initialized")
            except ImportError:
                logger.warning("SendGrid not installed")

    async def send_heatwave_alert(self, district: str, prediction: Dict[str, Any]):
        """Send all configured alerts for a heatwave prediction."""
        peak_day = max(prediction["forecast"], key=lambda x: x["severity_score"])
        severity = peak_day["severity"].upper()
        confidence = int(prediction["ensemble_confidence"] * 100)
        temp = peak_day["predicted_temp_max"]
        date = peak_day["date"]

        message = (
            f"🌡️ HEATWAVE ALERT — {district}\n"
            f"Severity: {severity} | Confidence: {confidence}%\n"
            f"Peak: {temp:.1f}°C on {date}\n"
            f"Vulnerable population at risk: "
            f"{prediction['health_risk'].get('vulnerable_population', 'N/A'):,}\n"
            f"Actions: {', '.join(prediction.get('recommended_actions', [])[:2])}"
        )

        results = []

        # SMS
        sms_result = await self._send_sms(district, message, prediction)
        results.append(sms_result)

        # Email
        email_result = await self._send_email(district, prediction, message)
        results.append(email_result)

        logger.info(f"📤 Alerts dispatched for {district}: {results}")
        return results

    async def _send_sms(self, district: str, message: str, prediction: Dict) -> Dict:
        """Send SMS via Twilio."""
        if not self._twilio_client:
            logger.info(f"[MOCK SMS] Would send to health officer of {district}:\n{message}")
            return {"type": "sms", "status": "mock_sent", "message": message[:100]}

        try:
            # In production: look up district health officer phone from DB
            recipient = "+919999999999"  # placeholder
            msg = self._twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=recipient,
            )
            return {"type": "sms", "status": "sent", "sid": msg.sid}
        except Exception as e:
            logger.error(f"SMS failed: {e}")
            return {"type": "sms", "status": "failed", "error": str(e)}

    async def _send_email(self, district: str, prediction: Dict, summary: str) -> Dict:
        """Send detailed email report via SendGrid."""
        if not self._sendgrid_client:
            logger.info(f"[MOCK EMAIL] Would send heatwave report for {district}")
            return {"type": "email", "status": "mock_sent"}

        try:
            from sendgrid.helpers.mail import Mail
            html_body = self._build_email_html(district, prediction)
            message = Mail(
                from_email=settings.ALERT_EMAIL_FROM,
                to_emails="health.officer@district.gov.in",
                subject=f"⚠️ Heatwave Alert — {district} — {prediction['forecast'][0]['date']}",
                html_content=html_body,
            )
            response = self._sendgrid_client.send(message)
            return {"type": "email", "status": "sent", "status_code": response.status_code}
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return {"type": "email", "status": "failed", "error": str(e)}

    def _build_email_html(self, district: str, prediction: Dict) -> str:
        """Build HTML email with forecast table and recommendations."""
        forecast_rows = ""
        for day in prediction["forecast"]:
            color = {
                "none": "#22c55e", "mild": "#eab308",
                "moderate": "#f97316", "severe": "#ef4444", "extreme": "#7c3aed"
            }.get(day["severity"], "#6b7280")
            forecast_rows += f"""
            <tr>
                <td style="padding:8px;border:1px solid #e5e7eb">{day['date']}</td>
                <td style="padding:8px;border:1px solid #e5e7eb">{day['predicted_temp_max']}°C</td>
                <td style="padding:8px;border:1px solid #e5e7eb">{int(day['heatwave_probability']*100)}%</td>
                <td style="padding:8px;border:1px solid #e5e7eb;color:{color};font-weight:bold">
                    {day['severity'].upper()}
                </td>
            </tr>"""

        actions = "".join(f"<li>{a}</li>" for a in prediction.get("recommended_actions", []))
        health = prediction.get("health_risk", {})

        return f"""
        <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
        <h2 style="color:#dc2626">🌡️ Heatwave Early Warning — {district}</h2>
        <p><strong>Prediction date:</strong> {prediction['prediction_date']}</p>
        <p><strong>Ensemble confidence:</strong> {int(prediction['ensemble_confidence']*100)}%</p>
        <h3>7-Day Forecast</h3>
        <table style="width:100%;border-collapse:collapse;font-size:14px">
            <tr style="background:#f3f4f6">
                <th style="padding:8px;border:1px solid #e5e7eb;text-align:left">Date</th>
                <th style="padding:8px;border:1px solid #e5e7eb;text-align:left">Max Temp</th>
                <th style="padding:8px;border:1px solid #e5e7eb;text-align:left">HW Prob</th>
                <th style="padding:8px;border:1px solid #e5e7eb;text-align:left">Severity</th>
            </tr>
            {forecast_rows}
        </table>
        <h3>Health Risk Assessment</h3>
        <ul>
            <li>Total population: {health.get('total_population',0):,}</li>
            <li>Vulnerable at risk: <strong>{health.get('vulnerable_population',0):,}</strong></li>
            <li>Elderly at risk: {health.get('elderly_at_risk',0):,}</li>
            <li>Children at risk: {health.get('children_at_risk',0):,}</li>
            <li>Risk level: <strong>{health.get('risk_level','').upper()}</strong></li>
        </ul>
        <h3>Recommended Actions</h3>
        <ul>{actions}</ul>
        <hr>
        <p style="color:#6b7280;font-size:12px">
            This alert was generated by the Heatwave Prediction System ML Engine.
            Confidence score above {int(settings.ALERT_CONFIDENCE_THRESHOLD*100)}% triggers this alert.
        </p>
        </body></html>
        """


class AlertRouter:
    """FastAPI router for alert endpoints."""
    pass
