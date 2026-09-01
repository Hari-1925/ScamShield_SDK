import sys
import os
import asyncio
import traceback
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "sdk")))
from scamshield import ScamShield
from scamshield.cloud.endpoints import CloudEndpoints

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

shield = ScamShield(
    api_key="scamshield-dev-key-2026",
    cloud_url="https://scamshield-sdk.onrender.com"
)

models_loaded = False

@app.on_event("startup")
async def startup_event():
    global models_loaded
    print("Warming up ScamShield AI models on Edge...")
    try:
        await shield.scan_text("warmup")
        models_loaded = True
        print("AI Models successfully loaded and ready.")
    except Exception as e:
        print(f"Error warming up models: {e}")

@app.get("/health")
async def health_check():
    if not models_loaded:
        return {"status": "loading", "message": "ScamShield Edge AI is currently loading..."}
    return {"status": "ready", "message": "ScamShield Edge AI Active"}

class LocalTextRequest(BaseModel):
    text: str
    contact_id: str = "unknown"

class CloudScanRequest(BaseModel):
    modality: str
    vectors: Dict[str, Any]
    gate_score: float

@app.post("/scan_local_text")
async def scan_local_text(msg: LocalTextRequest):
    if not models_loaded:
        return {"is_suspicious": False, "error": "AI models loading"}
    
    try:
        # In a real app, this would check the user's phone contacts.
        # For the demo, we assume incoming random chats are NOT saved contacts 
        # unless they have interacted heavily before.
        is_saved = False
        gate_res = shield.text_gate.run(msg.text, contact_id=msg.contact_id, is_saved_contact=is_saved)
        return {
            "is_scam": gate_res.passed_gate,
            "gate_score": gate_res.gate_score,
            "vectors": gate_res.vectors,
            "modality": "text"
        }
    except Exception as e:
        traceback.print_exc()
        return {"is_scam": False, "error": str(e)}

@app.post("/scan_local_media")
async def scan_local_media(file: UploadFile = File(...), contact_id: str = Form("unknown")):
    if not models_loaded:
        return {"is_scam": False, "error": "AI models loading"}

    content = await file.read()
    mime = file.content_type or ""

    try:
        if mime.startswith("image/"):
            gate_res = shield.image_gate.run(content)
            modality = "image"
        elif mime.startswith("audio/"):
            gate_res = shield.audio_gate.run(content, contact_id=contact_id)
            modality = "audio"
        elif mime.startswith("video/"):
            gate_res = shield.video_gate.run(content)
            modality = "video"
        else:
            return {"is_scam": False}

        return {
            "is_scam": gate_res.passed_gate,
            "gate_score": gate_res.gate_score,
            "vectors": gate_res.vectors,
            "modality": modality
        }
    except Exception as e:
        traceback.print_exc()
        return {"is_scam": False, "error": str(e)}

@app.post("/scan_cloud")
async def scan_cloud(req: CloudScanRequest):
    endpoints = {
        "text": CloudEndpoints.DETECT_TEXT,
        "image": CloudEndpoints.DETECT_IMAGE,
        "audio": CloudEndpoints.DETECT_AUDIO,
        "video": CloudEndpoints.DETECT_VIDEO
    }
    ep = endpoints.get(req.modality)
    if not ep:
        return {"alert_level": "green", "explanation": "Unknown modality"}

    try:
        res = await shield.cloud.detect(ep, req.vectors, req.gate_score)
        return res.model_dump() if hasattr(res, 'model_dump') else res.dict()
    except Exception as e:
        traceback.print_exc()
        return {
            "alert_level": "yellow",
            "explanation": f"Cloud verification failed. ({str(e) or repr(e)})"
        }

@app.websocket("/scan_call_stream")
async def scan_call_stream(websocket: WebSocket, contact_id: str = "unknown"):
    await websocket.accept()
    # Pass contact_id to start_audio_stream (which we'll update in SDK)
    session = await shield.start_audio_stream(contact_id=contact_id)
    
    async def listen_cloud_events():
        while session.is_active:
            if hasattr(session, 'event_queue') and session.event_queue:
                event = await session.event_queue.get()
                try:
                    await websocket.send_json(event)
                except Exception:
                    break
            else:
                await asyncio.sleep(0.5)

    event_task = asyncio.create_task(listen_cloud_events())
    
    try:
        while True:
            data = await websocket.receive_bytes()
            chunk_res = await session.send_chunk(data)
            
            if chunk_res.should_alert:
                await websocket.send_json({
                    "action": "LOCAL_WARNING",
                    "reason": "Edge AI suspects this is a scam. Verifying with Cloud...",
                    "score": chunk_res.running_score
                })
            else:
                await websocket.send_json({"action": "SAFE", "score": chunk_res.running_score})
                
    except WebSocketDisconnect:
        print("WebRTC Stream Scanner disconnected.")
    finally:
        session.is_active = False
        event_task.cancel()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
