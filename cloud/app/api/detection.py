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
    transcription: str
    gate_score: float
    session_id: Optional[str]

class ImageVectorRequest(BaseModel):
    ela_mean: float
    ela_std: float
    ela_max: float
    noise_std: float
    face_detected: bool
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
    transcription: str
    gate_score: float
    session_id: Optional[str]

async def process_detection(modality: str, req: BaseModel, request: Request, background_tasks: BackgroundTasks):
    app = request.app
    req_dict = req.dict()
    extracted_urls = req_dict.get("extracted_urls", [])
    
    tavily_task = asyncio.create_task(app.state.tavily.check_urls(extracted_urls))
    
    try:
        swytchcode_res = await app.state.swytchcode.run_pipeline(modality, req_dict, req.gate_score)
        cloud_score = swytchcode_res.get("confidence_score", 0.0)
        explanation = swytchcode_res.get("explanation", "")
        recommendation = swytchcode_res.get("recommendation", "")
        scam_type = swytchcode_res.get("scam_type")
    except Exception:
        lyzr_res = await app.state.lyzr.analyse(modality, req_dict, req.gate_score)
        cloud_score = lyzr_res.get("confidence_score", 0.0)
        scam_type = lyzr_res.get("scam_type")
        
        gemini_res = await app.state.gemini.build_fallback_explanation(cloud_score, scam_type)
        explanation = gemini_res.get("explanation", "")
        recommendation = gemini_res.get("recommendation", "")

    tavily_res = await tavily_task
    hits = tavily_res.get("hits", 0)
    
    boost = min(hits * 0.12, 0.25)
    final_score = min(cloud_score + boost, 1.0)
    
    alert_level = "none"
    if final_score >= 0.85: alert_level = "red"
    elif final_score >= 0.65: alert_level = "orange"
    elif final_score >= 0.40: alert_level = "yellow"

    incident_id = str(uuid.uuid4())

    if alert_level in ("orange", "red"):
        background_tasks.add_task(app.state.n8n.trigger_alert_workflow, {
            "incident_id": incident_id,
            "alert_level": alert_level,
            "modality": modality,
            "scam_type": scam_type,
            "confidence_score": final_score
        })

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
        "n8n_triggered": alert_level in ("orange", "red")
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
