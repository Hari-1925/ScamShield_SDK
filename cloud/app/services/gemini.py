import os
import json
from typing import Optional

class GeminiService:
    def __init__(self):
        try:
            from google import genai
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                self.is_configured = False
            else:
                self.client = genai.Client(api_key=api_key)
                self.model_name = "gemini-3.6-flash"
                self.is_configured = True
        except (ImportError, ValueError):
            self.is_configured = False

    async def fuse_and_explain(self, modality: str, gate_score: float, cloud_score: float, scam_type: Optional[str], threat_intel: dict) -> dict:
        if not self.is_configured:
            return self.build_fallback_explanation(cloud_score, scam_type)
            
        tavily_hits = threat_intel.get("hits", 0)
        evidence = threat_intel.get("evidence", [])
        evidence_snippet = json.dumps(evidence[:2])
        
        prompt = f"""
        You are a scam detection assistant protecting users from fraud and deepfakes.

        Analysis results:
        Modality: {modality}
        Local gate score: {gate_score}
        Cloud analysis score: {cloud_score}
        Detection category: {scam_type}
        Threat intelligence hits: {tavily_hits}
        Evidence: {evidence_snippet}

        Respond ONLY with valid JSON, no markdown:
        {{
          "explanation": "1-2 sentences in simple English.",
          "recommendation": "One specific action."
        }}
        """
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            # Remove potential markdown formatting from JSON response
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return self.build_fallback_explanation(cloud_score, scam_type)

    def build_fallback_explanation(self, score: float, scam_type: Optional[str]) -> dict:
        if score < 0.40:
            return {
                "explanation": "No significant threats detected.",
                "recommendation": "This content appears safe."
            }
        descriptions = {
            "upi_fraud": "This appears to be a UPI payment scam.",
            "bank_phishing": "This looks like a bank phishing attempt.",
            "otp_scam": "This message is trying to steal your OTP.",
            "lottery_prize": "This appears to be a lottery scam.",
            "job_scam": "This looks like a fraudulent job offer.",
            "romance_scam": "This shows signs of a romance scam.",
            "investment_scam": "This appears to be an investment fraud.",
            "deepfake_impersonation": "This may be an impersonation attempt.",
            "deepfake_audio": "This audio shows signs of AI generation.",
            "deepfake_video": "This video shows deepfake indicators.",
        }
        explanation = descriptions.get(scam_type, "Suspicious content detected.")
        return {
            "explanation": explanation,
            "recommendation": "Do not share personal information."
        }

    async def health_check(self) -> bool:
        return self.is_configured
