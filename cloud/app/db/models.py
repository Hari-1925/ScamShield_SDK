from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Text
from datetime import datetime
import uuid
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    modality = Column(String)
    scam_type = Column(String, nullable=True)
    gate_score = Column(Float)
    cloud_score = Column(Float, nullable=True)
    confidence_score = Column(Float)
    alert_level = Column(String)
    explanation = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    agent_scores = Column(Text, nullable=True) # JSON string
    threat_intel = Column(Text, nullable=True) # JSON string
    swytchcode_used = Column(Boolean, default=True)
    user_feedback = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    processed_locally = Column(Boolean, default=False)

class StreamSession(Base):
    __tablename__ = "stream_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    modality = Column(String) # audio/video
    chunks_processed = Column(Integer, default=0)
    peak_score = Column(Float, default=0.0)
    final_alert_level = Column(String, default="none")
    session_id = Column(String, nullable=True)
