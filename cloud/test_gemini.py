import asyncio
import os
import sys

# Load env
from dotenv import load_dotenv
load_dotenv(".env")

from app.services.gemini import GeminiService

async def main():
    service = GeminiService()
    if not service.is_configured:
        print("Service not configured. Please set GEMINI_API_KEY.")
        return
        
    print("Testing fusion...")
    result = await service.fuse_and_explain(
        modality="text",
        gate_score=0.9,
        cloud_score=0.95,
        scam_type="otp_scam",
        threat_intel={"hits": 2, "evidence": ["url: bad.com"]}
    )
    print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
