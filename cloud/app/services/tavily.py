import os
import httpx
import asyncio

class TavilyService:
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY", "")
        self.base_url = "https://api.tavily.com"

    async def _check_single_url(self, url: str) -> dict:
        async with httpx.AsyncClient(timeout=8) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/search",
                    json={
                        "api_key": self.api_key,
                        "query": f"scam phishing fraud site:{url} OR {url}",
                        "search_depth": "basic",
                        "max_results": 3,
                        "include_answer": False
                    }
                )
                if response.status_code == 200:
                    results = response.json().get("results", [])
                    hits = 0
                    evidence = []
                    scam_keywords = ["scam", "phishing", "fraud", "malware", "fake", "spam", "suspicious", "blacklist", "reported", "malicious", "unsafe"]
                    
                    for r in results:
                        content = r.get("content", "").lower()
                        if any(kw in content for kw in scam_keywords):
                            hits += 1
                            evidence.append({
                                "url": url,
                                "source": r.get("url"),
                                "snippet": r.get("content", "")[:200]
                            })
                    return {"hits": hits, "evidence": evidence}
                return {"hits": 0, "evidence": []}
            except Exception:
                return {"hits": 0, "evidence": []}

    async def check_urls(self, urls: list) -> dict:
        if not urls:
            return {"hits": 0, "evidence": [], "checked_urls": []}
        
        urls_to_check = urls[:3]
        tasks = [self._check_single_url(url) for url in urls_to_check]
        results = await asyncio.gather(*tasks)
        
        total_hits = sum(r["hits"] for r in results)
        total_evidence = []
        for r in results:
            total_evidence.extend(r["evidence"])
            
        return {
            "hits": total_hits,
            "evidence": total_evidence,
            "checked_urls": urls_to_check
        }

    async def search_scam_intel(self, query: str) -> dict:
        async with httpx.AsyncClient(timeout=8) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/search",
                    json={
                        "api_key": self.api_key,
                        "query": f"{query} scam fraud india",
                        "search_depth": "basic",
                        "max_results": 5
                    }
                )
                return response.json()
            except Exception:
                return {}

    async def health_check(self) -> bool:
        return True
