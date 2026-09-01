import asyncio
import sys
import os

sys.path.append(os.path.abspath('sdk'))
from scamshield.client import ScamShield
from scamshield.cloud.endpoints import CloudEndpoints

async def main():
    shield = ScamShield(api_key="scamshield-dev-key-2026", cloud_url="https://scamshield-sdk.onrender.com")
    shield.cloud.timeout = 120
    
    with open("tests/samples/lottery_scam.png", "rb") as f:
        img_bytes = f.read()
        
    gate_res = await shield.scan_image(img_bytes)
    print("Result:", gate_res)

asyncio.run(main())
