from scamshield.models import StreamChunkResult, DetectionResult, AlertLevel, VideoStreamSession
from scamshield.gate.video_gate import VideoGate
from scamshield.cloud.client import CloudClient
from scamshield.cloud.endpoints import CloudEndpoints

class VideoStreamClient(VideoStreamSession):
    def __init__(self, ws_url: str, api_key: str, video_gate: VideoGate, cloud_client: CloudClient = None):
        self.ws_url = ws_url
        self.api_key = api_key
        self.video_gate = video_gate
        self.cloud_client = cloud_client
        self.running_score = 0.0
        self.alert_level = AlertLevel.NONE
        self.face_detected = False
        self.is_active = True
        self.chunk_id = 0
        self.threshold = 0.30
        self.final_detection = None
        self.cloud_verified_severe_threat = False
        self.transcript_history = []
        
    async def connect(self):
        pass

    async def send_frame(self, frame_bytes: bytes, audio_bytes: bytes) -> StreamChunkResult:
        self.chunk_id += 1
        
        # Combine the last 15 seconds (5 chunks) of conversation history for semantic context
        context = " ".join(self.transcript_history[-5:])
        
        # We can reuse the AudioGate logic via VideoGate's internal audio_gate
        gate_res = self.video_gate.audio_gate.run(audio_bytes, context_history=context)
        
        new_text = gate_res.vectors.get("transcription", "").strip()
        if new_text:
            self.transcript_history.append(new_text)
        
        # Also optionally run ImageGate on the frame_bytes if provided
        frame_score = 0.0
        visual_tags = []
        if frame_bytes and len(frame_bytes) > 0:
            frame_res = self.video_gate.image_gate.run(frame_bytes, skip_ocr=True)
            frame_score = frame_res.gate_score
            self.face_detected = frame_res.vectors.get("face_detected", False)
            visual_tags = frame_res.vectors.get("visual_tags", [])
            
        gate_res.gate_score = max(gate_res.gate_score, frame_score)
        
        # Construct proper VideoVectorRequest payload
        video_vectors = {
            "frame_scores": [frame_score],
            "avg_frame_score": frame_score,
            "frames_analysed": 1,
            "audio_score": gate_res.gate_score,
            "audio_vectors": gate_res.vectors.copy(),
            "acoustic_tags": gate_res.vectors.get("acoustic_tags", []),
            "visual_tags": visual_tags,
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
                            CloudEndpoints.DETECT_VIDEO, 
                            video_vectors, 
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
            modality="video_stream"
        )
