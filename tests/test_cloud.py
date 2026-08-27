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
                print(f"  {svc}: {'✓' if ok else '✗'}")
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
                print("  PASSED ✓\n")
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
                print(f"  Data: {r.json()}")
                print("  PASSED ✓\n")
            else:
                print(f"  FAILED: {r.text}\n")
        except Exception as e:
            print(f"  FAILED: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_cloud())
