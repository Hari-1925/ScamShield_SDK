import io
import os
import tempfile
import numpy as np
from scamshield.models import GateResult
from scamshield.gate.text_gate import TextGate

class AudioGate:
    def __init__(self, text_gate: TextGate):
        self.whisper_model = None
        self.text_gate = text_gate

    def load(self):
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            print("Please install faster-whisper: pip install faster-whisper")
            return
            
        self.whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("Audio gate loaded")

    def run(self, audio_bytes: bytes) -> GateResult:
        import librosa
        import soundfile as sf
        
        # Step 1 - Load audio
        audio, sr = sf.read(io.BytesIO(audio_bytes))
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1) # to mono
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

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
        if np.mean(mfcc_std) < 8.0:
            score += 0.30
        if centroid > 4000:
            score += 0.20
        if pitch_std < 15.0:
            score += 0.25
        if energy_std < 0.05:
            score += 0.15
        acoustic_score = min(score, 1.0)

        # Step 4 - Transcribe
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
            
        try:
            segments, _ = self.whisper_model.transcribe(tmp_path, language="en")
            transcription = " ".join(s.text for s in segments)
        finally:
            os.remove(tmp_path)

        # Step 5 - Text gate on transcription
        text_result = self.text_gate.run(transcription)
        text_score = text_result.gate_score

        # Step 6 - Fuse
        gate_score = max(acoustic_score * 0.55 + text_score * 0.45, acoustic_score)

        return GateResult(
            passed_gate=gate_score >= 0.35,
            gate_score=float(gate_score),
            gate_reason="Acoustic and text analysis",
            vectors={
                "mfcc_mean": mfcc_mean.tolist(),
                "mfcc_std": mfcc_std.tolist(),
                "zcr": float(zcr),
                "spectral_centroid": float(centroid),
                "pitch_std": float(pitch_std),
                "energy_std": float(energy_std),
                "transcription": transcription,
                "text_vectors": text_result.vectors
            },
            modality="audio"
        )
