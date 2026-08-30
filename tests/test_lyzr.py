import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cloud'))
from app.services.lyzr import LyzrService

async def test_lyzr():
    env_path = os.path.join(os.path.dirname(__file__), '..', 'cloud', '.env')
    load_dotenv(dotenv_path=env_path)
    
    print("========================================")
    print("Testing Lyzr Agent Integration...")
    print("========================================")
    
    lyzr = LyzrService()
    
    if not lyzr.api_key:
        print("[FAILED] No LYZR_API_KEY found in cloud/.env")
        return
        
    print("[SUCCESS] Lyzr API Key loaded.")
    print("[SUCCESS] Lyzr API Key loaded.")
    print("\n[ORCHESTRATOR] Sending vectors to Lyzr v3 Agent Studio...")
    
    try:
        req_dict = {
            "transcription": "Your package is seized by customs pay 5000 rupees now",
            "scrubbed_transcription": "Your [PACKAGE] is seized by customs pay [AMOUNT] now",
            "keyword_hits": ["customs", "package", "urgent"],
            "acoustic_tags": ["Pitch variance: Monotone (Synthetic)", "Background noise: 0% (Studio condition)", "Breathing detected: False"],
            "visual_tags": ["Blink rate: 0 blinks in 15 seconds", "Lighting consistency: Mismatched jawline shadows", "Lip-sync: 45% (Desynchronized)"],
            "gate_score": 0.85
        }
        threat_intel = {
            "hits": 2,
            "evidence": ["Fake customs scam reported"]
        }
        
        cfo_res = await lyzr.orchestrate_multimodal_agents("video", req_dict, threat_intel)
        
        print("\n[SUCCESS] The Chief Fraud Officer has synthesized the reports!")
        print("\n--- Final CFO Verdict ---")
        print(f"Confidence Score: {cfo_res.get('confidence_score')}")
        print(f"Scam Type: {cfo_res.get('scam_type')}")
        print(f"Explanation: {cfo_res.get('explanation')}")
        print(f"Recommendation: {cfo_res.get('recommendation')}")
            
    except Exception as e:
        print(f"\n[FAILED] Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_lyzr())
