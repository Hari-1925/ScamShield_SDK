import asyncio
import os
import time
from scamshield import ScamShield

async def test_multimodal():
    shield = ScamShield(api_key="scamshield-dev-key", cloud_url="http://localhost:8000", model_dir="models", timeout=45)
    print("Pre-loading models...")
    
    # 1. Measure Model Load Time
    load_start = time.time()
    shield._ensure_models_loaded()
    load_end = time.time()
    print(f"\n[INFO] MODELS LOADED IN: {(load_end - load_start):.2f} seconds\n")
    
    samples_dir = "tests/samples"
    files = [
        # Audio
        "irl_scam.mp3",
        # Video
        "deepfake_videocall.mp4",
        "irl_scam.mp4"
    ]
    
    sep = "=" * 60
    
    for filename in files:
        filepath = os.path.join(samples_dir, filename)
        if not os.path.exists(filepath):
            continue
            
        print(f"\n{sep}")
        print(f"TESTING: {filename}")
        print(f"{sep}")
        
        ext = os.path.splitext(filename)[1].lower()
        
        # Calculate media duration
        media_duration = 0.0
        try:
            if ext in [".mp3", ".wav"]:
                import soundfile as sf
                media_duration = sf.info(filepath).duration
            elif ext in [".mp4", ".avi", ".mov"]:
                import cv2
                cap = cv2.VideoCapture(filepath)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                if fps > 0:
                    media_duration = frames / fps
                cap.release()
        except Exception:
            pass
            
        if media_duration > 0:
            print(f"Media Duration: {media_duration:.2f} seconds")
        
        try:
            with open(filepath, "rb") as f:
                content = f.read()
                
            start_time = time.time()
                
            if ext in [".mp3", ".wav"]:
                res = await shield.scan_audio(content)
            elif ext in [".png", ".jpg", ".jpeg"]:
                res = await shield.scan_image(content)
            elif ext in [".mp4", ".avi", ".mov"]:
                res = await shield.scan_video(content)
                
            end_time = time.time()
            elapsed_sec = (end_time - start_time)
                
            print(f"Processing Time: {elapsed_sec:.2f} seconds")
            
            # Extrapolate for 1 minute
            if media_duration > 0:
                time_per_minute = (elapsed_sec / media_duration) * 60.0
                print(f"[ESTIMATE] Time to process 1 MINUTE of this media: {time_per_minute:.2f} seconds")
                
            print(f"Gate Score (Local Threat Level): {res.gate_score:.3f}")
            print(f"Escalated to Cloud: {not res.processed_locally}")
            
            if not res.processed_locally:
                print(f"Cloud Verification Score: {res.cloud_score}")
                print(f"Lyzr Final Verdict: {res.explanation}")
                print(f"Recommendation: {res.recommendation}")
            else:
                print("DROPPED BY LOCAL GATE (Safe. Data never left the phone).")
            
        except Exception as e:
            import traceback
            print(f"Error processing {filename}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_multimodal())
