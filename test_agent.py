import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=150) as client:
        with open("tests/samples/lottery_scam.png", "rb") as f:
            files = {"file": ("lottery_scam.png", f, "image/png")}
            res = await client.post("http://localhost:8001/scan_media", files=files)
            print(res.status_code, res.text)

asyncio.run(main())
