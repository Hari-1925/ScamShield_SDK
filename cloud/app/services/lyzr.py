import os
import httpx
import json
import uuid

class LyzrService:
    def __init__(self):
        self.api_key = os.getenv("LYZR_API_KEY", "")
        self.base_url = "https://agent.api.lyzr.ai"

    async def analyse(self, modality: str, vectors: dict, gate_score: float) -> dict:
        async with httpx.AsyncClient(timeout=8) as client:
            message = f"Analyse these features: {json.dumps(vectors)}. Gate score: {gate_score}. Return JSON with confidence_score and scam_type."
            try:
                response = await client.post(
                    f"{self.base_url}/v2/chat/",
                    headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
                    json={
                        "user_id": "scamshield_cloud",
                        "agent_id": f"{modality}_detection_agent",
                        "session_id": str(uuid.uuid4()),
                        "message": message
                    }
                )
                response.raise_for_status()
                content = response.json()
                return content.get("response", {})
            except Exception as e:
                return {"confidence_score": gate_score, "scam_type": None}

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                return True
        except Exception:
            return False
