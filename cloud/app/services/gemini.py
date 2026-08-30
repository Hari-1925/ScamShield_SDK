import os
import json
import asyncio
from typing import Optional, Dict

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

    async def _call_agent(self, role_prompt: str, data: str) -> str:
        if not self.is_configured:
            return "Agent unavailable."
        prompt = f"{role_prompt}\n\nDATA:\n{data}\n\nProvide a concise analysis report."
        
        # Retry mechanism for 503 High Demand / Rate Limits
        for attempt in range(3):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text.strip()
            except Exception as e:
                if "503" in str(e) or "429" in str(e):
                    if attempt < 2:
                        await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
                        continue
                print(f"Agent Error (Attempt {attempt + 1}): {e}")
                return "Analysis failed due to API limits."

    async def agent_audio_forensic(self, vectors: dict) -> str:
        role = "You are the Audio Forensic Agent. Analyze these audio features (MFCC, pitch, ZCR, energy). Detect signs of AI-cloned voices, synthetic generation, or deepfakes. Keep your report to 2 sentences."
        return await self._call_agent(role, json.dumps(vectors))

    async def agent_vision_forensic(self, vectors: dict) -> str:
        role = "You are the Vision Forensic Agent. Analyze these image/video features (ELA scores, noise, face detection). Detect signs of face-swaps, digital manipulation, or visual deepfakes. Keep your report to 2 sentences."
        return await self._call_agent(role, json.dumps(vectors))

    async def agent_social_engineering(self, text_data: dict) -> str:
        role = "You are the Social Engineering Agent. Analyze the provided keywords and extracted text. Detect manipulation tactics like extreme urgency, authority impersonation (police/customs), or financial coercion. Keep your report to 2 sentences."
        return await self._call_agent(role, json.dumps(text_data))

    async def chief_fraud_officer(self, audio_report: str, vision_report: str, social_report: str, osint_report: str, modality: str) -> dict:
        if not self.is_configured:
            return self.build_fallback_explanation(0.0, None)
            
        prompt = f"""
        You are the Chief Fraud Officer of ScamShield. You are orchestrating a council of expert AI agents.
        
        Modality under investigation: {modality}
        
        --- SUB-AGENT REPORTS ---
        1. Audio Forensic Report: {audio_report}
        2. Vision Forensic Report: {vision_report}
        3. Social Engineering Report: {social_report}
        4. OSINT (Web Search) Report: {osint_report}
        
        Synthesize these reports and make a final determination.
        Respond ONLY with valid JSON, no markdown:
        {{
          "confidence_score": 0.0 to 1.0 (float, 1.0 being 100% scam),
          "scam_type": "name_of_scam_or_none",
          "explanation": "2-3 sentences summarizing the council's findings.",
          "recommendation": "One specific action."
        }}
        """
        # Retry mechanism for CFO
        for attempt in range(3):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                text = response.text.replace('```json', '').replace('```', '').strip()
                return json.loads(text)
            except Exception as e:
                if "503" in str(e) or "429" in str(e):
                    if attempt < 2:
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
                print(f"CFO Error (Attempt {attempt + 1}): {e}")
                return self.build_fallback_explanation(0.5, "unknown_error")

    async def orchestrate_multimodal_agents(self, modality: str, req_dict: dict, threat_intel: dict) -> dict:
        """Runs the agents in parallel and passes results to the Chief Fraud Officer."""
        audio_task = asyncio.create_task(self.agent_audio_forensic({
            "mfcc_mean": req_dict.get("mfcc_mean"),
            "zcr": req_dict.get("zcr"),
            "pitch_std": req_dict.get("pitch_std"),
            "audio_vectors": req_dict.get("audio_vectors")
        })) if modality in ["audio", "video"] else None
        
        vision_task = asyncio.create_task(self.agent_vision_forensic({
            "ela_mean": req_dict.get("ela_mean"),
            "face_detected": req_dict.get("face_detected"),
            "frame_scores": req_dict.get("frame_scores")
        })) if modality in ["image", "video"] else None
        
        social_task = asyncio.create_task(self.agent_social_engineering({
            "keyword_hits": req_dict.get("keyword_hits"),
            "ocr_text": req_dict.get("ocr_text")
        }))
        
        audio_rep = await audio_task if audio_task else "N/A (Not an audio payload)"
        vision_rep = await vision_task if vision_task else "N/A (Not a visual payload)"
        social_rep = await social_task
        osint_rep = f"Tavily Hits: {threat_intel.get('hits')}. Evidence: {json.dumps(threat_intel.get('evidence', [])[:2])}"
        
        # CFO makes the final decision
        return await self.chief_fraud_officer(audio_rep, vision_rep, social_rep, osint_rep, modality)

    def build_fallback_explanation(self, score: float, scam_type: Optional[str]) -> dict:
        if score < 0.35:
            return {
                "confidence_score": score,
                "scam_type": scam_type,
                "explanation": "No significant threats detected.",
                "recommendation": "This content appears safe."
            }
        return {
            "confidence_score": max(score, 0.75),
            "scam_type": scam_type or "suspicious_activity",
            "explanation": "Suspicious content detected by fallback system.",
            "recommendation": "Do not share personal information."
        }

    async def health_check(self) -> bool:
        return self.is_configured
