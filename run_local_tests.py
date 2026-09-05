import os
import sys
import time
import csv
from pathlib import Path

# Force UTF-8 encoding for Windows console to fix charmap printing errors
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add sdk to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "sdk"))

from scamshield.gate.text_gate import TextGate
from scamshield.gate.audio_gate import AudioGate
from scamshield.gate.image_gate import ImageGate
from scamshield.gate.video_gate import VideoGate

def main():
    print("=" * 70)
    print("SCAMSHIELD V3 - LOCAL EDGE TESTING SUITE")
    print("Zero Cloud Escalation. Testing Edge Models Only.")
    print("=" * 70)
    
    print("\n[1/4] Loading TextGate...")
    text_gate = TextGate()
    text_gate.load()
    
    print("[2/4] Loading AudioGate...")
    audio_gate = AudioGate(text_gate=text_gate)
    audio_gate.load()
    
    print("[3/4] Loading ImageGate...")
    image_gate = ImageGate(text_gate=text_gate)
    image_gate.load()
    
    print("[4/4] Loading VideoGate...")
    video_gate = VideoGate(image_gate=image_gate, audio_gate=audio_gate)
    
    print("\nAll models loaded successfully.\n")
    
    samples_dir = os.path.join("tests", "samples")
    text_dir = os.path.join(samples_dir, "Text")
    audio_dir = os.path.join(samples_dir, "Audio")
    video_dir = os.path.join(samples_dir, "Video")
    
    # 1. Test Text
    print("\n" + "=" * 70)
    print("=== Testing TEXT Samples ===")
    print("=" * 70)
    if os.path.exists(text_dir):
        for f in os.listdir(text_dir):
            if f.endswith(".csv"):
                print(f"\n--- File: {f} ---")
                file_path = os.path.join(text_dir, f)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        reader = csv.reader(file)
                        for i, row in enumerate(reader):
                            if not row: continue
                            text = row[0][:50] + "..." if len(row[0]) > 50 else row[0]
                            
                            start_time = time.time()
                            res = text_gate.run(row[0])
                            latency = time.time() - start_time
                            
                            print(f"Text [{i+1:02d}]: {text:<53} | Prob: {res.gate_score:.2f} | Latency: {latency*1000:.0f}ms")
                except Exception as e:
                    print(f"Error reading {f}: {e}")

    # 2. Test Audio
    print("\n" + "=" * 70)
    print("=== Testing AUDIO Samples ===")
    print("=" * 70)
    if os.path.exists(audio_dir):
        for f in os.listdir(audio_dir):
            if f.endswith(".mp3") or f.endswith(".wav"):
                file_path = os.path.join(audio_dir, f)
                try:
                    with open(file_path, "rb") as file:
                        audio_bytes = file.read()
                        
                    start_time = time.time()
                    res = audio_gate.run(audio_bytes)
                    latency = time.time() - start_time
                    
                    print(f"Audio: {f:<30} | Prob: {res.gate_score:.2f} | Latency: {latency*1000:.0f}ms")
                except Exception as e:
                    print(f"Error reading {f}: {e}")
                
    # 3. Test Video & Image
    print("\n" + "=" * 70)
    print("=== Testing VIDEO & IMAGE Samples ===")
    print("=" * 70)
    if os.path.exists(video_dir):
        for f in os.listdir(video_dir):
            if f.endswith(".mp4") or f.endswith(".webm") or f.endswith(".jpg") or f.endswith(".png"):
                file_path = os.path.join(video_dir, f)
                try:
                    with open(file_path, "rb") as file:
                        file_bytes = file.read()
                        
                    start_time = time.time()
                    if f.endswith(".mp4") or f.endswith(".webm"):
                        res = video_gate.run(file_bytes)
                        latency = time.time() - start_time
                        print(f"Video: {f:<30} | Prob: {res.gate_score:.2f} | Latency: {latency*1000:.0f}ms")
                    elif f.endswith(".jpg") or f.endswith(".png"):
                        res = image_gate.run(file_bytes)
                        latency = time.time() - start_time
                        print(f"Image: {f:<30} | Prob: {res.gate_score:.2f} | Latency: {latency*1000:.0f}ms")
                except Exception as e:
                    print(f"Error reading {f}: {e}")

if __name__ == "__main__":
    main()
