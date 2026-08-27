import os
import httpx

class SwytchcodeService:
    def __init__(self):
        self.api_url = os.getenv("SWYTCHCODE_API_URL", "https://api.swytchcode.com")
        self.api_key = os.getenv("SWYTCHCODE_API_KEY", "")
        self.workflow = "scamshield_detection_pipeline"

    async def run_pipeline(self, modality: str, vectors: dict, gate_score: float) -> dict:
        async with httpx.AsyncClient(timeout=8) as client:
            try:
                response = await client.post(
                    f"{self.api_url}/v1/workflows/{self.workflow}/execute",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "inputs": {
                            "modality": modality,
                            "vectors": vectors,
                            "gate_score": gate_score
                        }
                    }
                )
                response.raise_for_status()
                return response.json().get("outputs", {})
            except Exception as e:
                # Fallback handled in detection.py
                raise RuntimeError(f"Swytchcode Error: {e}")

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.api_url}/health")
                return resp.status_code == 200
        except Exception:
            return False
