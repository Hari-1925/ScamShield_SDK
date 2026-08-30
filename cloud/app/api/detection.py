import asyncio
import uuid
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class TextVectorRequest(BaseModel):
    embedding: List[float]
    keyword_hits: List[str]
    url_flags: List[str]
    extracted_urls: List[str]
    gate_score: float
    scam_category: Optional[str]
    session_id: Optional[str]

class AudioVectorRequest(BaseModel):
    mfcc_mean: List[float]
    mfcc_std: List[float]
    zcr: float
    spectral_centroid: float
    pitch_std: float
    energy_std: float
    acoustic_tags: List[str] = []
    transcription: str
    scrubbed_transcription: Optional[str] = ""
    keyword_hits: List[str] = []
    gate_score: float
    session_id: Optional[str]

class ImageVectorRequest(BaseModel):
    ela_mean: float
    ela_std: float
    ela_max: float
    noise_std: float
    face_detected: bool
    visual_tags: List[str] = []
    ocr_text: str
    ocr_score: float
    gate_score: float
    session_id: Optional[str]

class VideoVectorRequest(BaseModel):
    frame_scores: List[float]
    avg_frame_score: float
    frames_analysed: int
    audio_score: float
    audio_vectors: dict
    acoustic_tags: List[str] = []
    visual_tags: List[str] = []
    transcription: str
    scrubbed_transcription: Optional[str] = ""
    keyword_hits: List[str] = []
    gate_score: float
    session_id: Optional[str]

async def process_detection(modality: str, req: BaseModel, request: Request, background_tasks: BackgroundTasks):
    app = request.app
    req_dict = req.dict()
    extracted_urls = req_dict.get("extracted_urls", [])
    keyword_hits = req_dict.get("keyword_hits", [])
    
    # 1. URL Check (Safe, no PII)
    url_coro = app.state.tavily.check_urls(extracted_urls)
    tavily_url_task = asyncio.create_task(url_coro)
    
    # 2. Keyword Search (Safe, no PII)
    tavily_intel_task = None
    if keyword_hits:
        # Join keywords into a generic query (e.g. "FedEx customs arrest")
        query = " ".join(keyword_hits)
        intel_coro = app.state.tavily.search_scam_intel(query)
        tavily_intel_task = asyncio.create_task(intel_coro)
        
    try:
        swytchcode_res = await app.state.swytchcode.run_pipeline(modality, req_dict, req.gate_score)
        cloud_score = swytchcode_res.get("confidence_score", 0.0)
        explanation = swytchcode_res.get("explanation", "")
        recommendation = swytchcode_res.get("recommendation", "")
        scam_type = swytchcode_res.get("scam_type")
    except Exception:
        cloud_score = 0.0
        scam_type = None
        
        tavily_url_res = await tavily_url_task
        tavily_intel_res = await tavily_intel_task if tavily_intel_task else {}
        tavily_res = {
            "hits": tavily_url_res.get("hits", 0) + tavily_intel_res.get("hits", 0),
            "evidence": tavily_url_res.get("evidence", []) + tavily_intel_res.get("evidence", [])
        }
        
        # Trigger Lyzr Multi-Agent Orchestrator!
        cfo_res = await app.state.lyzr.orchestrate_multimodal_agents(
            modality=modality,
            req_dict=req_dict,
            threat_intel=tavily_res
        )
        cloud_score = cfo_res.get("confidence_score", cloud_score)
        scam_type = cfo_res.get("scam_type", scam_type)
        explanation = cfo_res.get("explanation", "")
        recommendation = cfo_res.get("recommendation", "")

    if 'tavily_res' not in locals():
        tavily_url_res = await tavily_url_task
        tavily_intel_res = await tavily_intel_task if tavily_intel_task else {}
        tavily_res = {
            "hits": tavily_url_res.get("hits", 0) + tavily_intel_res.get("hits", 0),
            "evidence": tavily_url_res.get("evidence", []) + tavily_intel_res.get("evidence", [])
        }
        
    hits = tavily_res.get("hits", 0)
    
    boost = min(hits * 0.12, 0.25)
    final_score = min(cloud_score + boost, 1.0)
    
    alert_level = "none"
    if final_score >= 0.85: alert_level = "red"
    elif final_score >= 0.65: alert_level = "orange"
    elif final_score >= 0.35: alert_level = "yellow"

    incident_id = str(uuid.uuid4())

    if alert_level in ("orange", "red"):
        # Alert systems can be plugged in here
        pass

    return {
        "incident_id": incident_id,
        "alert_level": alert_level,
        "confidence_score": final_score,
        "scam_type": scam_type,
        "explanation": explanation,
        "recommendation": recommendation,
        "gate_score": req.gate_score,
        "cloud_score": cloud_score,
        "processed_locally": False,
        "threat_intel_found": hits > 0,
        "modality": modality,
    }

@router.post("/detect/text")
async def detect_text(req: TextVectorRequest, request: Request, background_tasks: BackgroundTasks):
    return await process_detection("text", req, request, background_tasks)

@router.post("/detect/audio")
async def detect_audio(req: AudioVectorRequest, request: Request, background_tasks: BackgroundTasks):
    return await process_detection("audio", req, request, background_tasks)

@router.post("/detect/image")
async def detect_image(req: ImageVectorRequest, request: Request, background_tasks: BackgroundTasks):
    return await process_detection("image", req, request, background_tasks)

@router.post("/detect/video")
async def detect_video(req: VideoVectorRequest, request: Request, background_tasks: BackgroundTasks):
    return await process_detection("video", req, request, background_tasks)
