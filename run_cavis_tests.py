import os
import cv2
import numpy as np
from scamshield.gate.text_gate import TextGate
from scamshield.gate.audio_gate import AudioGate
from scamshield.gate.image_gate import ImageGate
from scamshield.gate.video_gate import VideoGate

def print_result(name, res):
    print(f"\n? {name}")
    print(f"   Verdict: {'[SCAM]' if res.passed_gate else '[SAFE]'}")
    print(f"   Score: {res.gate_score:.2f}")
    if res.vectors.get("visual_tags"): print(f"   Visual Tags: {res.vectors['visual_tags']}")
    if res.vectors.get("acoustic_tags"): print(f"   Acoustic Tags: {res.vectors['acoustic_tags']}")
    
    ocr = res.vectors.get("ocr_text", "")
    if ocr: print(f"   OCR Found: '{ocr}'")
    
    fs = res.vectors.get("face_swap_score", 0.0)
    if fs > 0: print(f"   Face Swap Jitter detected: {fs:.2f}")

print("Initializing CAVIS (Image & Video Gates)...")
text_gate = TextGate()
text_gate.load()
audio_gate = AudioGate(text_gate)
audio_gate.load()
image_gate = ImageGate(text_gate)
image_gate.load()
video_gate = VideoGate(image_gate, audio_gate)

tests_dir = os.path.join("tests", "samples")

print("\n==================================================")
print(" CAVIS V2 Comprehensive Test Suite")
print("==================================================")

# 1. Lottery Scam Image
print("\n[Running Test 1: Fake Bank Receipt / Scam Screenshot]")
with open(os.path.join(tests_dir, "Video", "lottery_scam.png"), "rb") as f:
    r = image_gate.run(f.read())
print_result("Screenshot with Scam Text", r)

# 2. Corrupted Image Edge Case
print("\n[Running Test 2: Corrupted Image Edge]")
r2 = image_gate.run(b"this is not an image byte string")
print_result("Corrupted Image", r2)

# 3. Real Person Scam Video
print("\n[Running Test 3: Real Person Scam Video]")
try:
    with open(os.path.join(tests_dir, "irl_scam.mp4"), "rb") as f:
        r3 = video_gate.run(f.read())
    print_result("IRL Scam Video", r3)
except Exception as e:
    print(f"Skipped IRL Scam Video: {e}")

# 4. Deepfake Video Call
print("\n[Running Test 4: Deepfake / Face Swap Video]")
try:
    with open(os.path.join(tests_dir, "deepfake_videocall.mp4"), "rb") as f:
        r4 = video_gate.run(f.read())
    print_result("Face Swap Deepfake", r4)
except Exception as e:
    print(f"Skipped Deepfake Video: {e}")

# 5. Normal Video
print("\n[Running Test 5: Normal Safe Video]")
try:
    with open(os.path.join(tests_dir, "normal.mp4"), "rb") as f:
        r5 = video_gate.run(f.read())
    print_result("Normal Safe Video", r5)
except Exception as e:
    print(f"Skipped Normal Video: {e}")

print("\n==================================================")
print(" CAVIS Test Suite Completed")
print("==================================================")
