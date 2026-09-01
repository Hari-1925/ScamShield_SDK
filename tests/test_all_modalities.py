import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sdk")))
from scamshield import ScamShield

async def run_tests():
    shield = ScamShield(
        api_key="scamshield-dev-key-2026",
        cloud_url="https://scamshield-sdk.onrender.com"
    )

    sep = "=" * 60
    print(f"\n{sep}")
    print("ScamShield Multimodal Edge-to-Cloud Test")
    print(f"{sep}\n")

    # 1. TEXT TEST
    print(">>> 1. Testing TEXT Modality (scam_message.txt)")
    try:
        with open("tests/samples/scam_message.txt", "r") as f:
            text = f.read()
        res = await shield.scan_text(text)
        print(f"Alert: {res.alert_level.upper()} | Score: {res.confidence_score}")
        print(f"Verdict: {res.explanation}\n")
    except Exception as e:
        print(f"Error testing text: {e}\n")

    # 2. IMAGE TEST
    print(">>> 2. Testing IMAGE Modality (lottery_scam.png)")
    try:
        with open("tests/samples/lottery_scam.png", "rb") as f:
            img_bytes = f.read()
        res = await shield.scan_image(img_bytes)
        print(f"Alert: {res.alert_level.upper()} | Score: {res.confidence_score}")
        print(f"Verdict: {res.explanation}\n")
    except Exception as e:
        print(f"Error testing image: {e}\n")

    # 3. AUDIO TEST
    print(">>> 3. Testing AUDIO Modality (irl_scam.mp3)")
    try:
        with open("tests/samples/irl_scam.mp3", "rb") as f:
            audio_bytes = f.read()
        res = await shield.scan_audio(audio_bytes)
        print(f"Alert: {res.alert_level.upper()} | Score: {res.confidence_score}")
        print(f"Verdict: {res.explanation}\n")
    except Exception as e:
        print(f"Error testing audio: {e}\n")

    # 4. VIDEO TEST
    print(">>> 4. Testing VIDEO Modality (deepfake_videocall.mp4)")
    try:
        with open("tests/samples/deepfake_videocall.mp4", "rb") as f:
            video_bytes = f.read()
        res = await shield.scan_video(video_bytes)
        print(f"Alert: {res.alert_level.upper()} | Score: {res.confidence_score}")
        print(f"Verdict: {res.explanation}\n")
    except Exception as e:
        print(f"Error testing video: {e}\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
