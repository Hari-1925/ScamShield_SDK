import asyncio
import httpx
import os
from dotenv import load_dotenv

# Try to load env if available
load_dotenv("cloud/.env")

BASE = "http://localhost:8000"

async def test_cloud():
    print("\nScamShield Cloud API Tests\n")

    async with httpx.AsyncClient() as client:

        print("TEST 1: Health endpoint")
        try:
            r = await client.get(f"{BASE}/health")
            data = r.json()
            print(f"  Status: {data.get('status')}")
            services = data.get("services", {})
            for svc, ok in services.items():
                print(f"  {svc}: {'OK' if ok else 'FAIL'}")
            print()
        except Exception as e:
            print(f"  FAILED: Could not connect to {BASE}/health. Is the server running? {e}\n")

        print("TEST 2: Text detection endpoint")
        try:
            r = await client.post(
                f"{BASE}/v1/detect/text",
                json={
                    "embedding": [0.1] * 384,
                    "keyword_hits": ["otp","urgent"],
                    "url_flags": ["bit.ly"],
                    "extracted_urls": ["bit.ly/test"],
                    "gate_score": 0.75,
                    "scam_category": "otp_scam",
                    "session_id": "test_cloud_001"
                },
                headers={"Authorization": f"Bearer {os.getenv('API_KEY','scamshield-dev-key-2026')}"}
            )
            print(f"  Status code: {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                print(f"  Alert: {d.get('alert_level')}")
                print(f"  Score: {d.get('confidence_score')}")
                print(f"  Swytchcode used: "
                      f"{d.get('swytchcode_used', False)}")
                print("  PASSED\n")
            else:
                print(f"  FAILED: {r.text}\n")
        except Exception as e:
            print(f"  FAILED: {e}\n")

        print("TEST 3: Stats endpoint")
        try:
            r = await client.get(
                f"{BASE}/v1/incidents/stats",
                headers={"Authorization": f"Bearer {os.getenv('API_KEY','scamshield-dev-key-2026')}"}
            )
            print(f"  Status: {r.status_code}")
            if r.status_code == 200:
                print("  PASSED\n")
            else:
                print(f"  FAILED: {r.text}\n")
        except Exception as e:
            print(f"  FAILED: {e}\n")
            
        print("TEST 4: Video detection endpoint with Semantic Forensic Tags (Deepfake attack)")
        try:
            r = await client.post(
                f"{BASE}/v1/detect/video",
                json={
                    "frame_scores": [0.99, 0.98],
                    "avg_frame_score": 0.985,
                    "frames_analysed": 2,
                    "audio_score": 0.9,
                    "audio_vectors": {},
                    "acoustic_tags": ["Pitch variance: Monotone (Synthetic)", "Background noise: 0% (Studio condition)", "Breathing detected: False"],
                    "visual_tags": ["Blink rate: 0 blinks in 15 seconds", "Lighting consistency: Mismatched jawline shadows", "Lip-sync: 45% (Desynchronized)"],
                    "transcription": "Your package is seized by customs pay 5000 rupees now",
                    "scrubbed_transcription": "Your [PACKAGE] is seized by customs pay [AMOUNT] now",
                    "keyword_hits": ["customs", "package", "urgent"],
                    "gate_score": 0.85,
                    "session_id": "test_cloud_002"
                },
                headers={"Authorization": f"Bearer {os.getenv('API_KEY','scamshield-dev-key-2026')}"},
                timeout=45.0
            )
            print(f"  Status code: {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                print(f"  Alert Level: {d.get('alert_level')}")
                print(f"  Final Score: {d.get('confidence_score')}")
                print(f"  Scam Type: {d.get('scam_type')}")
                print(f"  Explanation: {d.get('explanation')}")
                print(f"  Recommendation: {d.get('recommendation')}")
                print("  PASSED\n")
            else:
                print(f"  FAILED: {r.text}\n")
        except Exception as e:
            print(f"  FAILED: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_cloud())
