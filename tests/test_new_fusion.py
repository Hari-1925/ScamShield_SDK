import asyncio
import httpx

async def test_fusion():
    payload = {
        "embedding": [0.0] * 384,
        "keyword_hits": ["bank account", "suspended", "suspicious activity", "OTP", "verify"],
        "url_flags": [],
        "extracted_urls": [],
        "gate_score": 0.85,
        "scam_category": "otp_scam",
        "scrubbed_transcription": "Urgent! Your SBI bank account has been suspended due to suspicious activity. Share OTP received on your mobile to verify immediately.",
        "session_id": "test_session_123"
    }

    print("Testing new Parallel Lyzr + Tavily + Gemini Fusion...")
    async with httpx.AsyncClient(timeout=45) as client:
        try:
            res = await client.post("https://scamshield-sdk.onrender.com/v1/detect/text", json=payload)
            res.raise_for_status()
            print("\n? Final Report:")
            import json
            print(json.dumps(res.json(), indent=2))
        except Exception as e:
            print(f"Error: {e}")
            if hasattr(e, 'response') and e.response:
                print(e.response.text)

if __name__ == "__main__":
    asyncio.run(test_fusion())
