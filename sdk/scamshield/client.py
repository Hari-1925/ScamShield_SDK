import asyncio
from typing import Optional
from scamshield.models import (
    DetectionResult, AlertLevel,
    AudioStreamSession, VideoStreamSession
)
from scamshield.gate.text_gate import TextGate
from scamshield.gate.audio_gate import AudioGate
from scamshield.gate.image_gate import ImageGate
from scamshield.gate.video_gate import VideoGate
from scamshield.cloud.client import CloudClient
from scamshield.cloud.endpoints import CloudEndpoints

class ScamShield:
    def __init__(
        self,
        api_key: str,
        cloud_url: str = "https://scamshield.onrender.com",
        gate_threshold: float = 0.35,
        timeout: int = 180,
        model_dir: str = None
    ):
        self.api_key = api_key
        self.cloud_url = cloud_url
        self.gate_threshold = gate_threshold
        self.timeout = timeout
        self.model_dir = model_dir
        self.cloud = CloudClient(api_key, cloud_url, timeout)

        # Initialize local gates
        self.text_gate = TextGate(model_dir=self.model_dir)
        self.audio_gate = AudioGate(self.text_gate, model_dir=self.model_dir)
        self.image_gate = ImageGate(self.text_gate)
        self.video_gate = VideoGate(self.image_gate, self.audio_gate)

        self._models_loaded = False

    def _ensure_models_loaded(self):
        if not self._models_loaded:
            print("Downloading and loading models automatically on first run... This may take a moment.")
            self.text_gate.load()
            self.audio_gate.load()
            self.image_gate.load()
            self._models_loaded = True

    async def scan_text(self, text: str, session_id: str = None) -> DetectionResult:
        self._ensure_models_loaded()
        gate_res = self.text_gate.run(text)
        
        if not gate_res.passed_gate:
            return DetectionResult(
                incident_id=None,
                alert_level=AlertLevel.NONE,
                confidence_score=gate_res.gate_score,
                scam_type=None,
                explanation="Locally assessed as safe.",
                recommendation="No action needed.",
                gate_score=gate_res.gate_score,
                cloud_score=None,
                processed_locally=True,
                threat_intel_found=False,
                modality="text"
            )
            
        try:
            return await self.cloud.detect(CloudEndpoints.DETECT_TEXT, gate_res.vectors, gate_res.gate_score, session_id)
        except Exception as e:
            # Fallback if cloud fails completely
            return DetectionResult(
                incident_id=None,
                alert_level=AlertLevel.YELLOW,
                confidence_score=gate_res.gate_score,
                scam_type=None,
                explanation="Locally assessed as suspicious. Cloud verification failed.",
                recommendation="Proceed with caution.",
                gate_score=gate_res.gate_score,
                cloud_score=None,
                processed_locally=True,
                threat_intel_found=False,
                modality="text"
            )

    async def scan_image(self, image: bytes, session_id: str = None) -> DetectionResult:
        self._ensure_models_loaded()
        gate_res = self.image_gate.run(image)
        
        if not gate_res.passed_gate:
            return DetectionResult(
                incident_id=None,
                alert_level=AlertLevel.NONE,
                confidence_score=gate_res.gate_score,
                scam_type=None,
                explanation="Locally assessed as safe.",
                recommendation="No action needed.",
                gate_score=gate_res.gate_score,
                cloud_score=None,
                processed_locally=True,
                threat_intel_found=False,
                modality="image"
            )
            
        try:
            return await self.cloud.detect(CloudEndpoints.DETECT_IMAGE, gate_res.vectors, gate_res.gate_score, session_id)
        except Exception as e:
            return DetectionResult(
                incident_id=None,
                alert_level=AlertLevel.YELLOW,
                confidence_score=gate_res.gate_score,
                scam_type=None,
                explanation=f"Locally assessed as suspicious. Cloud verification failed. ({str(e) or repr(e)})",
                recommendation="Proceed with caution.",
                gate_score=gate_res.gate_score,
                cloud_score=None,
                processed_locally=True,
                threat_intel_found=False,
                modality="image"
            )

    async def scan_audio(self, audio: bytes, session_id: str = None) -> DetectionResult:
        self._ensure_models_loaded()
        gate_res = self.audio_gate.run(audio)
        
        if not gate_res.passed_gate:
            return DetectionResult(
                incident_id=None,
                alert_level=AlertLevel.NONE,
                confidence_score=gate_res.gate_score,
                scam_type=None,
                explanation="Locally assessed as safe.",
                recommendation="No action needed.",
                gate_score=gate_res.gate_score,
                cloud_score=None,
                processed_locally=True,
                threat_intel_found=False,
                modality="audio"
            )
            
        try:
            return await self.cloud.detect(CloudEndpoints.DETECT_AUDIO, gate_res.vectors, gate_res.gate_score, session_id)
        except Exception as e:
            return DetectionResult(
                incident_id=None,
                alert_level=AlertLevel.YELLOW,
                confidence_score=gate_res.gate_score,
                scam_type=None,
                explanation=f"Locally assessed as suspicious. Cloud verification failed. ({str(e) or repr(e)})",
                recommendation="Proceed with caution.",
                gate_score=gate_res.gate_score,
                cloud_score=None,
                processed_locally=True,
                threat_intel_found=False,
                modality="audio"
            )

    async def scan_video(self, video: bytes, session_id: str = None) -> DetectionResult:
        self._ensure_models_loaded()
        gate_res = self.video_gate.run(video)
        
        if not gate_res.passed_gate:
            return DetectionResult(
                incident_id=None,
                alert_level=AlertLevel.NONE,
                confidence_score=gate_res.gate_score,
                scam_type=None,
                explanation="Locally assessed as safe.",
                recommendation="No action needed.",
                gate_score=gate_res.gate_score,
                cloud_score=None,
                processed_locally=True,
                threat_intel_found=False,
                modality="video"
            )
            
        try:
            return await self.cloud.detect(CloudEndpoints.DETECT_VIDEO, gate_res.vectors, gate_res.gate_score, session_id)
        except Exception as e:
            return DetectionResult(
                incident_id=None,
                alert_level=AlertLevel.YELLOW,
                confidence_score=gate_res.gate_score,
                scam_type=None,
                explanation=f"Locally assessed as suspicious. Cloud verification failed. ({str(e) or repr(e)})",
                recommendation="Proceed with caution.",
                gate_score=gate_res.gate_score,
                cloud_score=None,
                processed_locally=True,
                threat_intel_found=False,
                modality="video"
            )

    async def start_audio_stream(self, contact_id: str = "unknown") -> AudioStreamSession:
        self._ensure_models_loaded()
        from scamshield.streaming.audio_stream import AudioStreamClient
        client = AudioStreamClient(
            ws_url=f"{self.cloud_url.replace('http', 'ws')}{CloudEndpoints.STREAM_AUDIO}",
            api_key=self.api_key,
            audio_gate=self.audio_gate,
            cloud_client=self.cloud,
            contact_id=contact_id
        )
        await client.connect()
        return client

    async def start_video_stream(self) -> VideoStreamSession:
        self._ensure_models_loaded()
        from scamshield.streaming.video_stream import VideoStreamClient
        client = VideoStreamClient(
            ws_url=f"{self.cloud_url.replace('http', 'ws')}{CloudEndpoints.STREAM_VIDEO}",
            api_key=self.api_key,
            video_gate=self.video_gate,
            cloud_client=self.cloud
        )
        await client.connect()
        return client

    async def report_false_positive(self, incident_id: str) -> bool:
        return await self.cloud.report_feedback(incident_id, "false_positive")

    async def confirm_threat(self, incident_id: str) -> bool:
        return await self.cloud.report_feedback(incident_id, "confirmed_threat")

    async def is_cloud_available(self) -> bool:
        try:
            return await self.cloud.check_health()
        except Exception:
            return False
        
    async def get_stats(self) -> dict:
        return await self.cloud.get_stats()
