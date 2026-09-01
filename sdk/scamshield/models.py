from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any

class AlertLevel(str, Enum):
    NONE   = "none"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED    = "red"

class GateResult(BaseModel):
    passed_gate: bool
    gate_score: float
    gate_reason: str
    vectors: Dict[str, Any]
    modality: str

class DetectionResult(BaseModel):
    incident_id: Optional[str]
    alert_level: AlertLevel
    confidence_score: float
    scam_type: Optional[str]
    explanation: str
    recommendation: str
    gate_score: float
    cloud_score: Optional[float]
    processed_locally: bool
    threat_intel_found: bool = False
    modality: str = "text"

    @property
    def should_alert(self) -> bool:
        return self.alert_level != AlertLevel.NONE

    @property
    def is_high_risk(self) -> bool:
        return self.alert_level in (
            AlertLevel.ORANGE,
            AlertLevel.RED
        )

class StreamChunkResult(BaseModel):
    chunk_id: int
    running_score: float
    alert_level: AlertLevel
    should_alert: bool
    transcription: str
    deepfake_score: float
    text_score: float
    explanation: str = ""
    n8n_triggered: bool = False

class AudioStreamSession:
    async def send_chunk(self, audio_bytes: bytes) -> StreamChunkResult:
        pass
    async def close(self) -> DetectionResult:
        pass
    running_score: float
    alert_level: AlertLevel
    is_active: bool

class VideoStreamSession:
    async def send_frame(self, frame_bytes: bytes, audio_bytes: bytes) -> StreamChunkResult:
        pass
    async def close(self) -> DetectionResult:
        pass
    running_score: float
    alert_level: AlertLevel
    face_detected: bool
