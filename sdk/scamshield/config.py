import os

class ScamShieldConfig:
    def __init__(self, api_key: str = None, cloud_url: str = None, gate_threshold: float = None, timeout: int = None):
        self.api_key = api_key or os.getenv("SCAMSHIELD_API_KEY", "")
        self.cloud_url = cloud_url or os.getenv("SCAMSHIELD_CLOUD_URL", "https://scamshield-sdk.onrender.com")
        self.gate_threshold = gate_threshold if gate_threshold is not None else 0.35
        self.timeout = timeout if timeout is not None else 180
