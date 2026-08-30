import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cloud'))
from app.services.gemini import GeminiService

async def test_gemini():
    env_path = os.path.join(os.path.dirname(__file__), '..', 'cloud', '.env')
    load_dotenv(dotenv_path=env_path)
    
    print("========================================")
    print("Testing Gemini 2.5 Flash Integration...")
    print("========================================")
    
    gemini = GeminiService()
    
    if not gemini.is_configured:
        print("[FAILED] No GEMINI_API_KEY found or google-genai is missing.")
        return
        
    print("[SUCCESS] Gemini API Key loaded.")
    print("\n[FUSION] Asking Gemini to explain a FedEx Scam...")
    
    try:
        res = await gemini.fuse_and_explain(
            modality="audio",
            gate_score=0.8,
            cloud_score=0.9,
            scam_type="customs_fraud",
            threat_intel={"hits": 5, "evidence": [{"snippet": "FedEx customs scam reported"}]}
        )
        
        print("\n[SUCCESS] Gemini successfully generated an explanation!")
        print("\n--- Output ---")
        print(f"Explanation: {res.get('explanation')}")
        print(f"Recommendation: {res.get('recommendation')}")
            
    except Exception as e:
        print(f"\n[FAILED] Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
