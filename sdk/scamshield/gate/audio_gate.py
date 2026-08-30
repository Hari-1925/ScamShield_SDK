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
                
        # Use device="auto" to enable GPU acceleration if available (massive latency drop)
        self.whisper_model = WhisperModel(model_name_or_path, device="auto", compute_type="default")
        print("Audio gate loaded")

    def run(self, audio_bytes: bytes, context_history: str = "") -> GateResult:
        import librosa
        import soundfile as sf
        
        # Step 1 - Load audio
        audio, sr = sf.read(io.BytesIO(audio_bytes))
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1) # to mono
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

        max_amp = np.max(np.abs(audio))
        
        # Skip analysis if it's pure digital silence to avoid false positives
        if max_amp < 0.001:
            return GateResult(
                passed_gate=False, gate_score=0.0, gate_reason="Silence",
                vectors={}, modality="audio"
            )

        # Step 2 - Extract features
        mfcc = librosa.feature.mfcc(y=audio, sr=16000, n_mfcc=40)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std  = np.std(mfcc, axis=1)
        zcr = np.mean(librosa.feature.zero_crossing_rate(audio))
        centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=16000))
        pitches, mags = librosa.piptrack(y=audio, sr=16000)
        pitch_vals = pitches[pitches > 0]
        pitch_std = np.std(pitch_vals) if len(pitch_vals) > 0 else 0.0
        energy_std = np.std(np.abs(audio))

        # Step 3 - Score deepfake likelihood
        score = 0.0
        
        # Only heavily penalize acoustic anomalies if there is actually speech (energy is high enough)
        # Live microphones often have silence or short bursts which artificially lower variance.
        is_active_speech = energy_std > 0.001
        
        if is_active_speech:
            if np.mean(mfcc_std) < 5.0:
                score += 0.20
            if centroid > 4500:
                score += 0.15
            if 0 < pitch_std < 10.0:  # Must be > 0 to avoid penalizing pure silence
                score += 0.20
            if energy_std < 0.02:
                score += 0.10
                
        acoustic_score = min(score, 1.0)

        # Step 4 - Semantic Feature Abstraction (Acoustic Tags)
        acoustic_tags = []
        if is_active_speech:
            if 0 < pitch_std < 10.0:
                acoustic_tags.append("Pitch variance: Monotone (Synthetic/Robotic)")
            else:
                acoustic_tags.append("Pitch variance: Natural")
                
            if np.mean(mfcc_std) < 5.0:
                acoustic_tags.append("Timbre: Unnaturally uniform (Potential Voice Cloning)")
            else:
                acoustic_tags.append("Timbre: Natural")
                
            if centroid > 4500:
                acoustic_tags.append("Spectrum: High frequency noise (Compression/GAN artifacts)")
        else:
            acoustic_tags.append("Audio: Mostly silence or background noise")
            
        if zcr > 0.15:
            acoustic_tags.append("Breathing patterns: Irregular or mechanical artifacts")
        else:
            acoustic_tags.append("Breathing patterns: Natural pauses detected")

        # Step 5 - Transcribe
        transcription = ""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
            
        try:
            # Add vad_filter=True to instantly skip silence, lowering latency
            segments, _ = self.whisper_model.transcribe(tmp_path, language="en", beam_size=1, vad_filter=True)
            transcription = " ".join(s.text for s in segments).strip()
        except Exception as e:
            print(f"[DEBUG AUDIO] Whisper Exception: {e}")
            transcription = ""
        finally:
            os.remove(tmp_path)

        # Step 6 - Text gate on transcription
        # Apply Rolling Semantic Window: Combine past context with current text
        full_semantic_text = f"{context_history} {transcription}".strip()
        
        # If there is no text at all, short-circuit
        if not full_semantic_text:
            return GateResult(
                passed_gate=False, gate_score=0.0, gate_reason="No speech detected",
                vectors={}, modality="audio"
            )
            
        text_result = self.text_gate.run(full_semantic_text)
        text_score = text_result.gate_score

        # Step 7 - Fuse
        # Use max instead of average so that if EITHER the audio is deepfaked
        # OR the transcript reveals a scam, it escalates.
        gate_score = max(acoustic_score, text_score)

        return GateResult(
            passed_gate=gate_score >= 0.30,
            gate_score=float(gate_score),
            gate_reason="Acoustic and text analysis",
            vectors={
                "mfcc_mean": mfcc_mean.tolist(),
                "mfcc_std": mfcc_std.tolist(),
                "zcr": float(zcr),
                "spectral_centroid": float(centroid),
                "pitch_std": float(pitch_std),
                "energy_std": float(energy_std),
                "acoustic_tags": acoustic_tags,
                "transcription": transcription,
                "scrubbed_transcription": text_result.vectors.get("scrubbed_transcription", ""),
                "keyword_hits": text_result.vectors.get("keyword_hits", []),
                "text_vectors": text_result.vectors
            },
            modality="audio"
        )
