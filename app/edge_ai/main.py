import sys
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Append root directory ScamShieldV3 to path so 'scamshield' can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from scamshield import ScamShield

app = FastAPI(title="ScamShield Edge AI")

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

class TextRequest(BaseModel):
    text: str
    session_id: str = "default_session"

@app.post("/scan/text")
async def scan_text(req: TextRequest):
    res = await shield.scan_text(req.text, req.session_id)
    return res.__dict__

@app.post("/scan/audio")
async def scan_audio(file: UploadFile = File(...), session_id: str = Form("default_session")):
    audio_bytes = await file.read()
    res = await shield.scan_audio(audio_bytes, session_id)
    return res.__dict__

@app.post("/scan/image")
async def scan_image(file: UploadFile = File(...), session_id: str = Form("default_session")):
    image_bytes = await file.read()
    res = await shield.scan_image(image_bytes, session_id)
    return res.__dict__

@app.post("/scan/video")
async def scan_video(file: UploadFile = File(...), session_id: str = Form("default_session")):
    video_bytes = await file.read()
    res = await shield.scan_video(video_bytes, session_id)
    return res.__dict__

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
