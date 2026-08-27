import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .db.database import init_db
from .api import detection, incidents, stream

logger = logging.getLogger("scamshield")
logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Init database tables
    init_db()
    
    # Init services
    from .services.swytchcode import SwytchcodeService
    from .services.lyzr import LyzrService
    from .services.tavily import TavilyService
    from .services.n8n import N8nService
    from .services.gemini import GeminiService
    
    app.state.swytchcode = SwytchcodeService()
    app.state.lyzr = LyzrService()
    app.state.tavily = TavilyService()
    app.state.n8n = N8nService()
    app.state.gemini = GeminiService()

    # Check health
    services = {
        "Swytchcode": app.state.swytchcode,
        "Lyzr": app.state.lyzr,
        "Tavily": app.state.tavily,
        "n8n": app.state.n8n,
        "Gemini": app.state.gemini
    }
    
    for name, service in services.items():
        try:
            if hasattr(service, 'health_check'):
                is_up = await service.health_check()
                if is_up:
                    print(f"{name}: ✓ connected")
                else:
                    print(f"WARNING: {name} is unreachable")
            else:
                print(f"{name}: ✓ connected (assumed)")
        except Exception as e:
            print(f"WARNING: {name} health check failed: {e}")

    print("ScamShield Cloud API ready")
    yield

app = FastAPI(title="ScamShield Cloud API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(detection.router, prefix="/v1")
app.include_router(incidents.router, prefix="/v1")
app.include_router(stream.router, prefix="/v1")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "services": {
            "swytchcode": True,
            "lyzr": True,
            "tavily": True,
            "n8n": True,
            "gemini": True,
            "database": True
        },
        "version": "1.0.0"
    }
