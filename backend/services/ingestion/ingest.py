from backend.domain.models import Email, EmailAudit
from backend.core.database import SessionLocal
from datetime import datetime
from backend.domain.interns import is_registered_intern


def ingest_email(sender: str, subject: str, body: str, message_id: str, email_date: datetime) -> bool:
    """
    Idempotent email ingestion with audit logging.
    Returns True if newly stored, False if duplicate or invalid sender.
    """

    db = SessionLocal()

    try:
        # 🔒 Hard filter: only allow registered interns
        if not is_registered_intern(sender):
            print(f"[SKIPPED] Non-intern email ignored: {sender}")
            return False

        # 🔍 Check duplicate via message_id
        existing = db.query(Email).filter(
            Email.message_id == message_id
        ).first()

        if existing:
            audit = EmailAudit(
                email_id=existing.id,
                event="DUPLICATE",
                details="Duplicate message_id detected during ingestion"
            )
            db.add(audit)
            db.commit()

            print(f"[SKIPPED] Duplicate email: {message_id}")
            return False

        # 🔥 Create new email entry
        new_email = Email(
            sender=sender,
            subject=subject,
            body=body,
            message_id=message_id,
            status="FETCHED",
            processed=0,
            retry_count=0,
            created_at=email_date if email_date else datetime.utcnow()
        )

        db.add(new_email)
        db.commit()
        db.refresh(new_email)

        # 🔎 Audit entry
        audit = EmailAudit(
            email_id=new_email.id,
            event="FETCHED",
            details="Email successfully fetched and stored"
        )
        db.add(audit)
        db.commit()

        print(f"[INGESTED] Email stored: {message_id}")
        return True

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Ingestion failed for {message_id}: {e}")
        return False

    finally:
        db.close()