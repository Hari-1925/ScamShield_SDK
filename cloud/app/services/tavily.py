import os
import asyncio
from tavily import AsyncTavilyClient

class TavilyService:
    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY", "")
        # Initialize the official SDK client
        self.client = AsyncTavilyClient(api_key=api_key) if api_key else None

    async def _check_single_url(self, url: str) -> dict:
        if not self.client:
            return {"hits": 0, "evidence": []}
            
        try:
            # We use Search to find if this URL is reported on scam forums
            response = await self.client.search(
                query=f"scam phishing fraud site:{url} OR {url}",
                search_depth="basic",
                max_results=3,
                include_answer=False
            )
            
            results = response.get("results", [])
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
        except Exception:
            return {"hits": 0, "evidence": []}

    async def check_urls(self, urls: list) -> dict:
        if not urls or not self.client:
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
        if not self.client:
            return {}
            
        try:
            # Use Search to find context about the scam script
            return await self.client.search(
                query=f"{query} scam fraud india",
                search_depth="basic",
                max_results=5
            )
        except Exception:
            return {}
            
    async def extract_suspicious_url(self, url: str) -> str:
        """Extracts clean HTML/text from a suspicious URL without clicking it."""
        if not self.client:
            return ""
            
        try:
            # Use Extract to safely read a phishing site's contents
            response = await self.client.extract(urls=[url])
            results = response.get("results", [])
            if results:
                return results[0].get("raw_content", "")[:2000]
            return ""
        except Exception:
            return ""

    async def health_check(self) -> bool:
        return self.client is not None
