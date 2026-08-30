import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from .db.database import init_db
from .api import detection, incidents, stream
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    from .services.gemini import GeminiService
    
    app.state.swytchcode = SwytchcodeService()
    app.state.lyzr = LyzrService()
    app.state.tavily = TavilyService()
    app.state.gemini = GeminiService()

    # Check health
    services = {
        "Swytchcode": app.state.swytchcode,
        "Lyzr": app.state.lyzr,
        "Tavily": app.state.tavily,
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
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(detection.router, prefix="/v1")
app.include_router(incidents.router, prefix="/v1")
app.include_router(stream.router, prefix="/v1")

@app.get("/health")
async def health_check(request: Request):
    app = request.app
    return {
        "status": "ok",
        "services": {
            "swytchcode": app.state.swytchcode.is_configured if hasattr(app.state.swytchcode, 'is_configured') else True,
            "lyzr": app.state.lyzr.is_configured if hasattr(app.state.lyzr, 'is_configured') else True,
            "tavily": app.state.tavily.is_configured if hasattr(app.state.tavily, 'is_configured') else True,
            "gemini": getattr(app.state.gemini, 'is_configured', False),
            "database": True
        },
        "version": "1.0.0"
    }
