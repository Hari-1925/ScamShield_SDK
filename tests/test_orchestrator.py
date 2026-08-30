import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cloud'))
from app.services.gemini import GeminiService

async def test_orchestrator():
    env_path = os.path.join(os.path.dirname(__file__), '..', 'cloud', '.env')
    load_dotenv(dotenv_path=env_path)
    
    print("========================================")
    print("Testing Multi-Agent Orchestrator...")
    print("========================================")
    
    gemini = GeminiService()
    
    if not gemini.is_configured:
        print("[FAILED] No GEMINI_API_KEY found or google-genai is missing.")
        return
        
    print("[SUCCESS] Gemini API Key loaded.")
    print("\n[ORCHESTRATOR] Spawning Vision, Audio, Social, and CFO Agents...")
    
    try:
        # Mocking a Video Deepfake Call
        req_dict = {
            "mfcc_mean": [0.5, 0.6], 
            "zcr": 0.05, 
            "pitch_std": 20.5,
            "ela_mean": 85.0, 
            "face_detected": True,
            "keyword_hits": ["urgent", "transfer", "police"]
        }
        threat_intel = {
            "hits": 3,
            "evidence": [{"snippet": "Police transfer scam reported recently"}]
        }
        
        # This will run the sub-agents in parallel and feed to the CFO
        cfo_res = await gemini.orchestrate_multimodal_agents("video", req_dict, threat_intel)
        
        print("\n[SUCCESS] The Chief Fraud Officer has synthesized the reports!")
        print("\n--- Final CFO Verdict ---")
        print(f"Confidence Score: {cfo_res.get('confidence_score')}")
        print(f"Scam Type: {cfo_res.get('scam_type')}")
        print(f"Explanation: {cfo_res.get('explanation')}")
        print(f"Recommendation: {cfo_res.get('recommendation')}")
            
    except Exception as e:
        print(f"\n[FAILED] Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
