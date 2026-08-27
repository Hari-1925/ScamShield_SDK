import os
import httpx
from datetime import datetime

class N8nService:
    def __init__(self):
        self.webhook_base = os.getenv("N8N_WEBHOOK_BASE_URL", "https://n8n.example.com")
        self.api_key = os.getenv("N8N_API_KEY", "")

    async def trigger_alert_workflow(self, incident: dict) -> bool:
        async with httpx.AsyncClient(timeout=5) as client:
            incident["timestamp"] = datetime.utcnow().isoformat()
            try:
                await client.post(
                    f"{self.webhook_base}/webhook/scamshield-alert",
                    json=incident
                )
                return True
            except Exception:
                return False

    async def trigger_false_positive_workflow(self, incident_id: str, feedback: str) -> bool:
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                await client.post(
                    f"{self.webhook_base}/webhook/scamshield-feedback",
                    json={
                        "incident_id": incident_id,
                        "feedback": feedback,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                return True
            except Exception:
                return False

    async def trigger_daily_report_workflow(self) -> bool:
        async with httpx.AsyncClient(timeout=5) as client:
            try:
                await client.post(
                    f"{self.webhook_base}/webhook/scamshield-daily-report",
                    json={
                        "date": datetime.utcnow().isoformat(),
                        "trigger": "daily_schedule"
                    }
                )
                return True
            except Exception:
                return False

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                res = await client.get(f"{self.webhook_base}/webhook/scamshield-health")
                return res.status_code == 200
        except Exception:
            return False
