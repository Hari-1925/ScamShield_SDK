import os
import numpy as np
from scamshield.gate.text_gate import TextGate
from scamshield.gate.audio_gate import AudioGate

def print_result(name, res):
    print(f"\n? {name}")
    print(f"   Verdict: {'[SCAM]' if res.passed_gate else '[SAFE]'}")
    print(f"   Reason: {res.gate_reason}")
    print(f"   Overall Score: {res.gate_score:.2f}")
    if res.vectors:
        ac_score = res.vectors.get("acoustic_score", 0.0)
        txt_score = res.vectors.get("text_score", 0.0)
        print(f"   Acoustic Score: {ac_score:.2f} | Text Score: {txt_score:.2f}")
        tags = res.vectors.get("acoustic_tags", [])
        if tags: print(f"   Acoustic Tags: {tags}")
        txt = res.vectors.get("transcription", "")
        if txt: print(f"   Transcription: '{txt}'")

print("Initializing DAVE Audio Gate...")
text_gate = TextGate()
text_gate.load()
audio_gate = AudioGate(text_gate)
audio_gate.load()

tests_dir = os.path.join("tests", "samples")

print("\n==================================================")
print(" ScamShield Audio Gate (DAVE) Comprehensive Test")
print("==================================================")

# 1. Silence Test
print("\n[Running Test 1: Silence/Empty]")
silence = np.zeros(16000 * 3, dtype=np.float32) # 3 seconds
import io, soundfile as sf
buf = io.BytesIO()
sf.write(buf, silence, 16000, format='WAV', subtype='PCM_16')
res_silence = audio_gate.run(buf.getvalue(), contact_id="test_silence")
print_result("Silence Edge Case", res_silence)

# 2. TTS Voice Clone
print("\n[Running Test 2: TTS / Voice Clone (tts.mp3)]")
tts_path = os.path.join(tests_dir, "tts.mp3")
if os.path.exists(tts_path):
    with open(tts_path, "rb") as f:
        res_tts = audio_gate.run(f.read(), contact_id="test_tts")
    print_result("TTS / Voice Clone", res_tts)
else:
    print("Skipped: tts.mp3 not found")

# 3. Real Human Scam
print("\n[Running Test 3: IRL Human Scam (irl_scam.mp3)]")
scam_path = os.path.join(tests_dir, "irl_scam.mp3")
if os.path.exists(scam_path):
    with open(scam_path, "rb") as f:
        res_scam = audio_gate.run(f.read(), contact_id="test_human_scam")
    print_result("Human Scam (Semantic Trigger)", res_scam)
else:
    print("Skipped: irl_scam.mp3 not found")

# 4. Normal Safe Conversation
print("\n[Running Test 4: Normal Conversation (normal.mp3)]")
normal_path = os.path.join(tests_dir, "normal.mp3")
if os.path.exists(normal_path):
    with open(normal_path, "rb") as f:
        res_norm = audio_gate.run(f.read(), contact_id="test_safe")
    print_result("Normal Human Conversation", res_norm)
else:
    print("Skipped: normal.mp3 not found")

print("\n==================================================")
print(" Test Suite Completed")
print("==================================================")
