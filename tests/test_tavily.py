import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the cloud directory to the path so we can import the app
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cloud'))

from app.services.tavily import TavilyService

async def test_tavily():
    # Load the keys from cloud/.env
    env_path = os.path.join(os.path.dirname(__file__), '..', 'cloud', '.env')
    load_dotenv(dotenv_path=env_path)
    
    print("========================================")
    print("Testing Tavily Web Search Integration...")
    print("========================================")
    
    tavily = TavilyService()
    
    if not tavily.client:
        print("[FAILED] No TAVILY_API_KEY found in cloud/.env")
        return
        
    print("[SUCCESS] Tavily API Key loaded.")
    print("\n[SEARCH] Running live web search for: 'fake fedex customs call'")
    
    try:
        # Test 1: Search for a known scam context
        res = await tavily.search_scam_intel('fake fedex customs call')
        
        results = res.get('results', [])
        print(f"\n[SUCCESS] Found {len(results)} results from the live web!")
        
        for i, r in enumerate(results[:3], 1):
            print(f"\n--- Result {i} ---")
            print(f"URL: {r.get('url')}")
            print(f"Content: {r.get('content')[:300]}...")
            
    except Exception as e:
        print(f"\n[FAILED] Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_tavily())
