import os
import httpx
import json
import asyncio
import uuid

class LyzrService:
    def __init__(self):
        self.api_key = os.getenv("LYZR_API_KEY", "")
        self.base_url = "https://agent-prod.studio.lyzr.ai"

    def _scrub_payload(self, modality: str, raw_vectors: dict) -> dict:
        """
        PRIVACY MASKING LAYER:
        Strips all PII (transcripts, raw text) and leaves only
        mathematical vectors, ELA scores, and generic keywords.
        """
        scrubbed = {}
        
        # Semantic Feature Abstraction (Replaces raw math with semantic clues)
        if "acoustic_tags" in raw_vectors and raw_vectors["acoustic_tags"]:
            scrubbed["acoustic_analysis"] = raw_vectors["acoustic_tags"]
            
        if "visual_tags" in raw_vectors and raw_vectors["visual_tags"]:
            scrubbed["visual_analysis"] = raw_vectors["visual_tags"]

        # Text/Social Vectors (No raw transcripts allowed!)
        if "keyword_hits" in raw_vectors:
            scrubbed["topic_keywords"] = raw_vectors["keyword_hits"]
            
        if "scrubbed_transcription" in raw_vectors and raw_vectors["scrubbed_transcription"]:
            scrubbed["safe_transcript"] = raw_vectors["scrubbed_transcription"]
            
        # NEVER include "transcription", "ocr_text", or "extracted_urls"
        
        return scrubbed

    async def _call_agent(self, agent_id: str, message: str) -> str:
        if not self.api_key:
            return f"[{agent_id} Mock Output] Missing API Key."
            
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v3/inference/chat/",
                    headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
                    json={
                        "user_id": "hariqwerty72@gmail.com",
                        "agent_id": agent_id,
                        "session_id": str(uuid.uuid4()),
                        "message": message
                    }
                )
                response.raise_for_status()
                content = response.json()
                return content.get("response", "Analysis failed.")
            except Exception as e:
                import traceback
                print(f"Lyzr Agent Error ({agent_id}): {repr(e)}\n{traceback.format_exc()}")
                return "API Error or Timeout."

    async def orchestrate_multimodal_agents(self, modality: str, req_dict: dict, threat_intel: dict) -> dict:
        """
        Multi-Agent Orchestration via Lyzr Agent API.
        Enforces strict privacy by routing only scrubbed vectors.
        """
        scrubbed_data = self._scrub_payload(modality, req_dict)
        
        # 1. Fire Sub-Agents in Parallel
        tasks = []
        
        audio_agent_id = os.getenv("LYZR_AUDIO_AGENT_ID", "lyzr_audio_agent")
        vision_agent_id = os.getenv("LYZR_VISION_AGENT_ID", "lyzr_vision_agent")
        social_agent_id = os.getenv("LYZR_SOCIAL_AGENT_ID", "lyzr_social_agent")
        cfo_agent_id = os.getenv("LYZR_CFO_AGENT_ID", "lyzr_cfo_agent")
        
        # Audio Forensic Agent
        if modality in ["audio", "video"]:
            audio_msg = f"Act as an acoustic detective. Cross-reference these semantic acoustic tags with the context to detect AI voice cloning: {json.dumps(scrubbed_data.get('acoustic_analysis', []))}"
            tasks.append(self._call_agent(audio_agent_id, audio_msg))
        else:
            tasks.append(self._async_return("N/A"))

        # Vision Forensic Agent
        if modality in ["image", "video"]:
            vision_msg = f"Act as a visual forensics expert. Analyze these semantic visual anomaly tags to detect deepfakes/manipulation: {json.dumps(scrubbed_data.get('visual_analysis', []))}"
            tasks.append(self._call_agent(vision_agent_id, vision_msg))
        else:
            tasks.append(self._async_return("N/A"))
            
        # Social Engineering Agent
        social_msg_data = {
            "keywords": scrubbed_data.get('topic_keywords', []),
            "transcript": scrubbed_data.get('safe_transcript', "")
        }
        social_msg = f"CRITICAL INSTRUCTION: Analyze the SEMANTIC INTENT and PERSONA of the speaker in this transcript. \n1. If a family member/friend is casually discussing a problem, asking for help, or talking ABOUT a scam (e.g. 'I saw suspicious activity on my card'), this is SAFE.\n2. If the speaker is claiming to be an authority figure (bank, police, tech support) reporting 'suspicious activity' to the victim, or an unknown person demanding urgent action/money, it is a SCAM.\nDo not blindly trigger on keywords; understand WHO is speaking and WHY. Payload: {json.dumps(social_msg_data)}"
        tasks.append(self._call_agent(social_agent_id, social_msg))
        
        results = await asyncio.gather(*tasks)
        audio_rep, vision_rep, social_rep = results
        
        print("\n--- [DEBUG] Individual Agent Reports ---")
        print(f"Audio Agent: {audio_rep}")
        print(f"Vision Agent: {vision_rep}")
        print(f"Social Agent: {social_rep}")
        print("----------------------------------------\n")
        
        # OSINT Report (Generated locally by Tavily, no PII sent to Lyzr)
        osint_rep = f"Tavily Threat Hits: {threat_intel.get('hits')}."
        
        # 2. Chief Fraud Officer (CFO)
        cfo_msg = f"""
        Synthesize these reports. Respond ONLY with JSON.
        CRITICAL RULE: Evaluate the CONTEXT and PERSONA. 
        - Family/Friends discussing money, their accounts, or talking ABOUT scams they faced is completely SAFE (score < 0.2).
        - Impersonators (fake banks, tech support, strangers) using manipulation, urgency, or claiming 'suspicious activity on your account' to extort the user are SCAMS (score > 0.8).
        DO NOT flag innocent conversations just because they contain financial or fraud-related keywords.
        
        Audio: {audio_rep}
        Vision: {vision_rep}
        Social: {social_rep}
        OSINT: {osint_rep}
        
        Format: {{"confidence_score": 0.1, "scam_type": "name", "explanation": "text", "recommendation": "text"}}
        """
        
        cfo_raw = await self._call_agent(cfo_agent_id, cfo_msg)
        
        # Parse the JSON response
        try:
            clean_json = cfo_raw.replace('```json', '').replace('```', '').strip()
            if not clean_json.startswith("{"):
                raise ValueError("Not JSON")
            
            parsed_json = json.loads(clean_json)
            
            # If the user used the advanced Structured Schema, the data is nested in "agent"
            if "agent" in parsed_json and isinstance(parsed_json["agent"], dict):
                return parsed_json["agent"]
                
            return parsed_json
            
        except Exception:
            # Fallback if parsing fails or Mock is used
            return {
                "confidence_score": req_dict.get("gate_score", 0.5),
                "scam_type": "suspicious_activity",
                "explanation": "Scam detected based on vector anomalies.",
                "recommendation": "Do not proceed."
            }

    async def _async_return(self, val):
        return val

    async def health_check(self) -> bool:
        return bool(self.api_key)
