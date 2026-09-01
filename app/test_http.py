import asyncio
import httpx

async def test():
    try:
        async with httpx.AsyncClient() as c:
            res = await c.get('https://scamshield-sdk.onrender.com/health')
            print(res.status_code, res.text)
    except Exception as e:
        print("ERROR:", e)

asyncio.run(test())
