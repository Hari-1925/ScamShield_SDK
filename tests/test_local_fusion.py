import sys
import os
import asyncio
from fastapi import BackgroundTasks

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cloud")))

from app.api.detection import process_detection, TextVectorRequest
from app.services.tavily import TavilyService
from app.services.gemini import GeminiService
from app.services.lyzr import LyzrService

class MockSwytchcode:
    async def run_pipeline(self, *args):
        raise Exception("Mocking Swytchcode Failure to trigger Fallback Fusion")

class MockApp:
    def __init__(self):
        self.state = type('State', (), {})()

class MockRequest:
    def __init__(self, app):
        self.app = app

async def test_fusion():
    app = MockApp()
    app.state.tavily = TavilyService()
    app.state.gemini = GeminiService()
    app.state.lyzr = LyzrService()
    app.state.swytchcode = MockSwytchcode()
    
    req = TextVectorRequest(
        embedding=[0.0] * 384,
        keyword_hits=["bank account", "suspended", "suspicious activity", "OTP", "verify"],
        url_flags=[],
        extracted_urls=[],
        gate_score=0.85,
        scam_category="otp_scam",
        scrubbed_transcription="Urgent! Your SBI bank account has been suspended due to suspicious activity. Share OTP received on your mobile to verify immediately.",
        session_id="test_session_123"
    )
    
    request = MockRequest(app)
    bg_tasks = BackgroundTasks()

    print("Running Parallel Lyzr + Tavily + Gemini Fusion locally...")
    res = await process_detection("text", req, request, bg_tasks)
    
    import json
    print("\nFinal Report:")
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "../cloud/.env"))
    asyncio.run(test_fusion())
