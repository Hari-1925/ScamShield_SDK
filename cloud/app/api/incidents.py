from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel

router = APIRouter()

class FeedbackRequest(BaseModel):
    incident_id: str
    feedback: str

@router.get("/incidents/")
async def list_incidents():
    return {"incidents": []}

@router.get("/incidents/stats")
async def get_stats():
    return {"total": 0, "false_positives": 0}

@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    return {"incident_id": incident_id, "status": "not_found"}

@router.post("/incidents/feedback")
async def submit_feedback(req: FeedbackRequest, request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(
        request.app.state.n8n.trigger_false_positive_workflow,
        req.incident_id,
        req.feedback
    )
    return {"status": "accepted"}

@router.get("/daily-report")
async def trigger_daily_report(request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(request.app.state.n8n.trigger_daily_report_workflow)
    return {"status": "scheduled"}
