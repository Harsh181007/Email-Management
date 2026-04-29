from fastapi import FastAPI
from collections import defaultdict
from backend.platform_adapter.adapter import get_platform_snapshot
from backend.core.config import validate_config
from backend.core.database import Base, engine, SessionLocal
from backend.domain.models import Email, WorkUpdate
from backend.services.ingestion.ingest import ingest_email
from backend.services.tracking.tracker import process_email
from backend.services.risk.risk import compute_risk
from backend.services.tracking.progress import get_intern_progress
from backend.scheduler.jobs import start_scheduler
from backend.services.email.job_tracker import job_status

from pydantic import BaseModel
from datetime import datetime
import threading

# -------------------------------------------------
# FASTAPI APP
# -------------------------------------------------
app = FastAPI(title="Email Visibility System")

# -------------------------------------------------
# DATABASE INIT
# -------------------------------------------------
Base.metadata.create_all(bind=engine)

# -------------------------------------------------
# REQUEST MODELS
# -------------------------------------------------
class EmailIngestRequest(BaseModel):
    sender: str
    subject: str
    body: str

# -------------------------------------------------
# HEALTH
# -------------------------------------------------
@app.get("/health")
def health():
    return {"status": "running"}

# -------------------------------------------------
# EMAIL INGEST
# -------------------------------------------------
@app.post("/email/ingest")
def ingest(req: EmailIngestRequest):
    ingest_email(req.sender, req.subject, req.body)
    return {"message": "Email ingested"}

# -------------------------------------------------
# BACKGROUND JOB FUNCTION
# -------------------------------------------------
def run_email_job():

    db = SessionLocal()

    job_status["is_running"] = True
    job_status["last_status"] = "running"

    try:
        emails = db.query(Email).filter(Email.processed == 0).all()

        processed_count = 0

        for email in emails:
            process_email(email.id)
            processed_count += 1

        job_status["last_status"] = f"success ({processed_count} emails)"

    except Exception as e:
        job_status["last_status"] = f"failed: {str(e)}"

    finally:
        job_status["is_running"] = False
        job_status["last_run"] = datetime.now()
        db.close()

# -------------------------------------------------
# PROCESS EMAILS (ASYNC)
# -------------------------------------------------
@app.post("/email/process")
def process():

    if job_status["is_running"]:
        return {"message": "Processing already running"}

    thread = threading.Thread(target=run_email_job)
    thread.start()

    return {"message": "Processing started"}

# -------------------------------------------------
# JOB STATUS ENDPOINT
# -------------------------------------------------
@app.get("/email/status")
def get_status():
    return job_status

# -------------------------------------------------
# HR UPDATES
# -------------------------------------------------
@app.get("/hr/updates")
def hr_view():
    db = SessionLocal()
    updates = db.query(WorkUpdate).all()
    db.close()

    return [
        {
            "intern_id": u.intern_id,
            "project": u.project,
            "status": u.status,
            "summary": u.summary,
            "time": u.created_at.isoformat()
        }
        for u in updates
    ]

# -------------------------------------------------
# HR RISK VIEW
# -------------------------------------------------
@app.get("/hr/risk")
def hr_risk_view():
    db = SessionLocal()
    updates = db.query(WorkUpdate).all()
    db.close()

    grouped = defaultdict(list)
    for u in updates:
        grouped[u.intern_id].append(u)

    return {
        intern_id: compute_risk(ups)
        for intern_id, ups in grouped.items()
    }

# -------------------------------------------------
# INTERN PROGRESS
# -------------------------------------------------
@app.get("/hr/intern/{intern_email}")
def intern_progress(intern_email: str):
    return {
        "intern": intern_email,
        "progress": get_intern_progress(intern_email)
    }

# -------------------------------------------------
# PLATFORM INTEGRATION
# -------------------------------------------------
@app.get("/integration/platform/snapshot")
def platform_snapshot():
    return get_platform_snapshot()

# -------------------------------------------------
# SCHEDULER STARTUP
# -------------------------------------------------
@app.on_event("startup")
def startup_event():
    validate_config()
    start_scheduler()