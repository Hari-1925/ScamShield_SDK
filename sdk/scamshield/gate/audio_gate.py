import io
import os
import tempfile
import numpy as np
from scamshield.models import GateResult
from scamshield.gate.text_gate import TextGate

class AudioGate:
    def __init__(self, text_gate: TextGate, model_dir: str = None):
        self.model_dir = model_dir
        self.whisper_model = None
        self.text_gate = text_gate

    def load(self):
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            print("Please install faster-whisper: pip install faster-whisper")
            return
            
        model_name_or_path = "tiny"
        if self.model_dir:
            local_path = os.path.join(self.model_dir, "whisper-tiny")
            if os.path.exists(local_path):
                model_name_or_path = local_path
                
        self.whisper_model = WhisperModel(model_name_or_path, device="auto", compute_type="default")
        print("Audio gate loaded (DAVE Architecture)")

    def run(self, audio_bytes: bytes, contact_id: str = "unknown") -> GateResult:
        import librosa
        
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
            
        try:
            try:
                audio, sr = librosa.load(tmp_path, sr=16000, mono=True)
            except Exception as e:
                return GateResult(passed_gate=False, gate_score=0.0, gate_reason=f"Decode error: {e}", vectors={}, modality="audio")

            # 1. Pre-processor & VAD (RMS Energy thresholding)
            rms = librosa.feature.rms(y=audio)[0]
            mean_rms = np.mean(rms)
            
            if mean_rms < 0.005:  # Tightened VAD threshold for empty/silent chunks
                return GateResult(
                    passed_gate=False, gate_score=0.0, gate_reason="Silence / No Speech Detected",
                    vectors={}, modality="audio"
                )

            # 2. Path 1: Acoustic Anti-Spoofing Heuristics (Mimicking a lightweight CNN / AASist)
            pitches, mags = librosa.piptrack(y=audio, sr=16000)
            pitch_vals = pitches[pitches > 0]
            pitch_std = np.std(pitch_vals) if len(pitch_vals) > 0 else 0.0
            
            # Extract Spectral Flux to detect phase anomalies typical in AI Voice Clones (ElevenLabs etc.)
            onset_env = librosa.onset.onset_strength(y=audio, sr=16000)
            flux_variance = np.var(onset_env)
            
            acoustic_score = 0.0
            acoustic_tags = []
            
            # Rule 1: Robotic TTS (Absolutely flat pitch variance)
            if 0 < pitch_std < 8.0:
                acoustic_score += 0.50
                acoustic_tags.append("Pitch variance: Monotone (Synthetic/Robotic)")
            elif pitch_std >= 8.0:
                acoustic_tags.append("Pitch variance: Natural Human")
                
            # Rule 2: AI Voice Clones (Unnaturally smooth spectral flux / lacking micro-dynamics)
            if flux_variance < 0.5 and mean_rms > 0.01:
                acoustic_score += 0.40
                acoustic_tags.append("Timbre: Micro-dynamics missing (Potential AI Voice Clone)")
                
            acoustic_score = min(acoustic_score, 1.0)

            # 3. Path 2: Semantic Intent (Fast-Whisper + CAHS-Gate V2)
            transcription = ""
            try:
                segments, _ = self.whisper_model.transcribe(tmp_path, language="en", beam_size=1, vad_filter=True)
                transcription = " ".join(s.text for s in segments).strip()
            except Exception as e:
                print(f"[DEBUG AUDIO] Whisper Exception: {e}")
                transcription = ""

            text_score = 0.0
            text_vectors = {}
            if transcription:
                # Pass to CAHS-Gate V2 with contact_id for Historical Context RAG!
                # Assuming is_saved_contact based on whether it's not "unknown" for this demo
                is_saved = contact_id != "unknown"
                text_result = self.text_gate.run(transcription, contact_id=contact_id, is_saved_contact=is_saved, sender="them")
                text_score = text_result.gate_score
                text_vectors = text_result.vectors

            # 4. Fusion Engine
            gate_score = max(acoustic_score, text_score)

            reason_parts = []
            if acoustic_score > 0.4: reason_parts.append(f"Acoustic Anomaly ({acoustic_score:.2f})")
            if text_score > 0.4: reason_parts.append(f"Semantic Scam Intent ({text_score:.2f})")
            reason = " and ".join(reason_parts) if reason_parts else "Safe Audio"

            return GateResult(
                passed_gate=gate_score >= 0.35, # Tightened threshold
                gate_score=float(gate_score),
                gate_reason=reason,
                vectors={
                    "acoustic_score": float(acoustic_score),
                    "text_score": float(text_score),
                    "acoustic_tags": acoustic_tags,
                    "transcription": transcription,
                    "scrubbed_transcription": text_vectors.get("scrubbed_transcription", ""),
                    "keyword_hits": text_vectors.get("keyword_hits", []),
                    "text_vectors": text_vectors,
                    "trust_score": text_vectors.get("trust_score", 0.1)
                },
                modality="audio"
            )
        finally:
            if os.path.exists(tmp_path):
                try: os.remove(tmp_path)
                except: pass
