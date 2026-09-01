import asyncio
import sys
import os

sys.path.append(os.path.abspath('sdk'))
from scamshield.client import ScamShield
from scamshield.cloud.endpoints import CloudEndpoints

async def main():
    shield = ScamShield(api_key="scamshield-dev-key-2026", cloud_url="https://scamshield-sdk.onrender.com")
    shield.text_gate.load()
    # Run gate manually
    gate_res = shield.text_gate.run("Hi i am calling from sbi regarding a suspicious activity in your account")
    print("Vectors:", gate_res.vectors.keys())
    print("Gate Score:", gate_res.gate_score)
    
    try:
        cloud_res = await shield.cloud.detect(CloudEndpoints.DETECT_TEXT, gate_res.vectors, gate_res.gate_score, None)
        print("Cloud Res:", cloud_res)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
