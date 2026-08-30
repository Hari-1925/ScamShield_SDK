from scamshield.models import StreamChunkResult, DetectionResult, AlertLevel, AudioStreamSession
from scamshield.gate.audio_gate import AudioGate
from scamshield.cloud.client import CloudClient
from scamshield.cloud.endpoints import CloudEndpoints

class AudioStreamClient(AudioStreamSession):
    def __init__(self, ws_url: str, api_key: str, audio_gate: AudioGate, cloud_client: CloudClient = None):
        self.ws_url = ws_url
        self.api_key = api_key
        self.audio_gate = audio_gate
        self.cloud_client = cloud_client
        self.running_score = 0.0
        self.alert_level = AlertLevel.NONE
        self.is_active = True
        self.chunk_id = 0
        self.threshold = 0.30
        self.final_detection = None
        self.cloud_verified_severe_threat = False
        self.transcript_history = []
        
    async def connect(self):
        pass

    async def send_chunk(self, audio_bytes: bytes) -> StreamChunkResult:
        self.chunk_id += 1
        
        # Combine the last 15 seconds (5 chunks) of conversation history for semantic context
        context = " ".join(self.transcript_history[-5:])
        
        # Run local offline gate on this 3-second chunk
        gate_res = self.audio_gate.run(audio_bytes, context_history=context)
        
        new_text = gate_res.vectors.get("transcription", "").strip()
        if new_text:
            self.transcript_history.append(new_text)
        
        # Construct proper AudioVectorRequest payload
        audio_vectors = {
            "mfcc_mean": gate_res.vectors.get("mfcc_mean", [0.0] * 40),
            "mfcc_std": gate_res.vectors.get("mfcc_std", [0.0] * 40),
            "zcr": gate_res.vectors.get("zcr", 0.0),
            "spectral_centroid": gate_res.vectors.get("spectral_centroid", 0.0),
            "pitch_std": gate_res.vectors.get("pitch_std", 0.0),
            "energy_std": gate_res.vectors.get("energy_std", 0.0),
            "acoustic_tags": gate_res.vectors.get("acoustic_tags", []),
            "transcription": gate_res.vectors.get("transcription", ""),
            "scrubbed_transcription": gate_res.vectors.get("scrubbed_transcription", ""),
            "keyword_hits": gate_res.vectors.get("keyword_hits", []),
            "gate_score": gate_res.gate_score
        }

        self.running_score = max(self.running_score, gate_res.gate_score)
        should_alert = self.running_score >= self.threshold
        
        if should_alert:
            self.alert_level = AlertLevel.RED if self.running_score > 0.6 else AlertLevel.ORANGE
            
            # --- REAL-TIME CLOUD ESCALATION ---
            if self.cloud_client and not getattr(self, '_is_escalating', False):
                self._is_escalating = True
                # Run cloud verification in background without blocking the live stream
                import asyncio
                async def _bg_escalate():
                    try:
                        print("\n[⚡ ESCALATING TO CLOUD VERIFICATION] Please wait for Lyzr Final Verdict...\n")
                        cloud_res = await self.cloud_client.detect(
                            CloudEndpoints.DETECT_AUDIO, 
                            audio_vectors, 
                            self.running_score, 
                            session_id=None
                        )
                        self.final_detection = cloud_res
                        if cloud_res.cloud_score is not None:
                            # Override local score with Lyzr's definitive verdict (can lower or raise it)
                            self.running_score = cloud_res.cloud_score
                            
                            # Update Alert Level based on definitive cloud score
                            if self.running_score >= 0.8:
                                self.alert_level = AlertLevel.RED
                                self.cloud_verified_severe_threat = True
                            elif self.running_score >= 0.6:
                                self.alert_level = AlertLevel.ORANGE
                                self.cloud_verified_severe_threat = False
                            else:
                                self.alert_level = AlertLevel.NONE
                                self.cloud_verified_severe_threat = False
                                
                        print(f"\n[⚡ CLOUD VERDICT RECEIVED] Threat Level adjusted to: {self.running_score}\n")
                    except Exception as e:
                        print(f"[Cloud Escalation Failed] {e}")
                    finally:
                        self._is_escalating = False
                
                asyncio.create_task(_bg_escalate())
            
        transcription = gate_res.vectors.get("transcription", "")
            
        return StreamChunkResult(
            chunk_id=self.chunk_id,
            running_score=self.running_score,
            alert_level=self.alert_level,
            should_alert=should_alert,
            transcription=transcription,
            deepfake_score=gate_res.vectors.get("acoustic_score", 0.0),
            text_score=gate_res.vectors.get("text_score", 0.0)
        )

    async def close(self) -> DetectionResult:
        self.is_active = False
        
        if self.final_detection:
            return self.final_detection
            
        return DetectionResult(
            incident_id=None,
            alert_level=self.alert_level,
            confidence_score=self.running_score,
            scam_type=None,
            explanation=f"Stream closed. Final score: {self.running_score}",
            recommendation="Review the transcription." if self.running_score >= self.threshold else "No action needed.",
            gate_score=self.running_score,
            cloud_score=None,
            processed_locally=True,
            threat_intel_found=False,
            modality="audio_stream"
        )
