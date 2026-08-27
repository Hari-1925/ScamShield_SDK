import httpx
from typing import Dict, Any, Optional
from scamshield.models import DetectionResult
from scamshield.cloud.endpoints import CloudEndpoints

class CloudClient:
    def __init__(self, api_key: str, base_url: str, timeout: int = 10):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def detect(self, endpoint: str, vectors: dict, gate_score: float, session_id: Optional[str] = None) -> DetectionResult:
        payload = vectors.copy()
        payload["gate_score"] = gate_score
        payload["session_id"] = session_id
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                headers=self._headers()
            )
            response.raise_for_status()
            return DetectionResult(**response.json())

    async def report_feedback(self, incident_id: str, feedback: str = "false_positive") -> bool:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}{CloudEndpoints.INCIDENTS_FEEDBACK}",
                json={"incident_id": incident_id, "feedback": feedback},
                headers=self._headers()
            )
            return response.status_code == 200

    async def check_health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}{CloudEndpoints.HEALTH}")
                return response.status_code == 200
        except Exception:
            return False

    async def get_stats(self) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}{CloudEndpoints.INCIDENTS_STATS}",
                headers=self._headers()
            )
            response.raise_for_status()
            return response.json()
