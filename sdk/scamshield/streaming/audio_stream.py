import asyncio
from scamshield.models import StreamChunkResult, DetectionResult, AlertLevel, AudioStreamSession
from scamshield.gate.audio_gate import AudioGate
from scamshield.cloud.client import CloudClient
from scamshield.cloud.endpoints import CloudEndpoints

class AudioStreamClient(AudioStreamSession):
    def __init__(self, ws_url: str, api_key: str, audio_gate: AudioGate, cloud_client: CloudClient = None, contact_id: str = "unknown"):
        self.ws_url = ws_url
        self.api_key = api_key
        self.audio_gate = audio_gate
        self.cloud_client = cloud_client
        self.contact_id = contact_id
        self.running_score = 0.0
        self.alert_level = AlertLevel.NONE
        self.is_active = True
        self.chunk_id = 0
        self.threshold = 0.55
        self.final_detection = None
        self.cloud_verified_severe_threat = False
        self.transcript_history = []
        self.event_queue = None
        
    async def connect(self):
        self.event_queue = asyncio.Queue()

    async def send_chunk(self, audio_bytes: bytes) -> StreamChunkResult:
        self.chunk_id += 1
        
        # AudioGate V2 handles context history internally via sqlite, so we pass contact_id
        gate_res = self.audio_gate.run(audio_bytes, contact_id=self.contact_id)
        
        new_text = gate_res.vectors.get("transcription", "").strip()
        if new_text:
            self.transcript_history.append(new_text)
        
        audio_vectors = {
            # DAVE Fields
            "acoustic_score": gate_res.vectors.get("acoustic_score", 0.0),
            "text_score": gate_res.vectors.get("text_score", 0.0),
            "text_vectors": gate_res.vectors.get("text_vectors", {}),
            "trust_score": gate_res.vectors.get("trust_score", 0.1),
            
            "acoustic_tags": gate_res.vectors.get("acoustic_tags", []),
            "transcription": gate_res.vectors.get("transcription", ""),
            "scrubbed_transcription": gate_res.vectors.get("scrubbed_transcription", ""),
            "keyword_hits": gate_res.vectors.get("keyword_hits", []),
            "gate_score": gate_res.gate_score
        }

        self.running_score = max(self.running_score, gate_res.gate_score)
        should_alert = self.running_score >= self.threshold
        explanation = ""
        
        if should_alert:
            self.alert_level = AlertLevel.RED if self.running_score > 0.6 else AlertLevel.ORANGE
            explanation = "Local Edge AI suspects malicious activity."
            
            if not getattr(self, '_is_escalating', False) and not self.cloud_verified_severe_threat:
                self._is_escalating = True
                
                async def _bg_escalate():
                    try:
                        print("\n[?? LOCAL ESCALATION] Generating Local LLM Explanation...\n")
                        
                        # INSTANT UI UPDATE: Trigger the Red Banner immediately with zero latency!
                        if self.event_queue:
                            await self.event_queue.put({
                                "action": "CLOUD_VERDICT",
                                "explanation": "Local AI Explainer: Analyzing threat details...",
                                "is_scam": True,
                                "score": self.running_score
                            })
                        
                        # BACKGROUND GENERATION: Let the LLM take a few seconds to write the detailed text
                        loop = asyncio.get_event_loop()
                        try:
                            from scamshield.explainers.local_llm import explainer_instance
                            explanation_text = await loop.run_in_executor(
                                None, 
                                explainer_instance.explain, 
                                audio_vectors, 
                                self.running_score
                            )
                        except Exception as e:
                            explanation_text = f"Local AI Explainer: Detected malicious activity (Score: {self.running_score:.2f})"
                            
                        # ASYNC UI UPDATE: Replace the "Analyzing" text with the actual LLM generated text seamlessly
                        if self.event_queue:
                            await self.event_queue.put({
                                "action": "CLOUD_VERDICT",
                                "explanation": explanation_text,
                                "is_scam": True,
                                "score": self.running_score
                            })
                        
                        self.cloud_verified_severe_threat = True
                        print("\n[?? LOCAL VERDICT GENERATED]\n")
                            
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        print(f"[Local Escalation Failed] {repr(e)}")
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
            text_score=gate_res.vectors.get("text_score", 0.0),
            explanation=explanation
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
