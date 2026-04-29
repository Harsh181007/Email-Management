from backend.integrations.llm import llm_summarise
from backend.core.database import SessionLocal
from backend.domain.models import Email, WorkUpdate
from datetime import datetime
from backend.services.summarisation.summarise import summarise_email

def process_email(email_id: int):
    db = SessionLocal()

    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        db.close()
        return

    # 🔴 PREVENT DUPLICATE PROCESSING
    if email.processed == 1:
        db.close()
        return

    intern_email = email.sender.strip().lower()

    summary = summarise_email(
        email.body,
        llm_fallback=llm_summarise
    )

    work_update = WorkUpdate(
        email_id=email.id,
        intern_id=intern_email,
        project=email.subject,
        status="IN_PROGRESS",
        summary=summary,
        created_at=email.created_at
    )

    email.processed = 1

    db.add(work_update)
    db.commit()
    db.close()