from backend.core.database import SessionLocal
from backend.domain.models import EmailAudit

def log_audit(email_id: int, event: str, details: str = ""):
    db = SessionLocal()
    db.add(
        EmailAudit(
            email_id=email_id,
            event=event,
            details=details
        )
    )
    db.commit()
    db.close()
