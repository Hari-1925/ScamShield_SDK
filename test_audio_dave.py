import numpy as np
import scipy.io.wavfile as wav
import tempfile
import asyncio
from scamshield.gate.text_gate import TextGate
from scamshield.gate.audio_gate import AudioGate

text_gate = TextGate()
text_gate.load()
audio_gate = AudioGate(text_gate)
audio_gate.load()

# Create fake silence
fs = 16000
silence = np.zeros(16000, dtype=np.float32)

# Create a fake "robotic" tone (pure sine wave, zero pitch variance)
t = np.linspace(0, 1, 16000, endpoint=False)
robotic = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

def to_bytes(audio_array):
    import io, soundfile as sf
    buf = io.BytesIO()
    sf.write(buf, audio_array, 16000, format='WAV', subtype='PCM_16')
    return buf.getvalue()

print("\n--- Test 1: Silence ---")
r1 = audio_gate.run(to_bytes(silence))
print("Passed?", r1.passed_gate, "| Reason:", r1.gate_reason)

print("\n--- Test 2: Robotic Tone (Simulating TTS) ---")
r2 = audio_gate.run(to_bytes(robotic))
print("Passed?", r2.passed_gate, "| Score:", r2.gate_score, "| Tags:", r2.vectors["acoustic_tags"])

