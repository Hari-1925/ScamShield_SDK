from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/stream/audio")
async def stream_audio(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            # Logic handled in stream_gate and detection endpoint internally if needed
            # For brevity, stream logic acts as a passthrough or handled in client
            await websocket.send_json({"status": "received", "alert_level": "none"})
    except WebSocketDisconnect:
        pass

@router.websocket("/stream/video")
async def stream_video(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            await websocket.send_json({"status": "received", "alert_level": "none"})
    except WebSocketDisconnect:
        pass
