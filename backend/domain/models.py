from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from backend.core.database import Base

# -------------------------
# EMAIL MODEL
# -------------------------
class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String)
    subject = Column(String)
    body = Column(Text)
    message_id = Column(String, unique=True, index=True)
    status = Column(String, index=True)  
    processed = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    reminder_sent = Column(Integer, default=0)

    last_error = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


# -------------------------
# WORK UPDATE (USED BY HR DASHBOARD)
# -------------------------
class WorkUpdate(Base):
    __tablename__ = "work_updates"

    id = Column(Integer, primary_key=True, index=True)
    intern_id = Column(String, index=True)
    project = Column(String)
    status = Column(String)
    summary = Column(Text)
    email_id = Column(Integer, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# -------------------------
# AUDIT TRAIL
# -------------------------
class EmailAudit(Base):
    __tablename__ = "email_audit"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer)
    event = Column(String)  # FETCHED, PROCESSED, FAILED, RETRY_EXHAUSTED
    details = Column(Text)

    timestamp = Column(DateTime, default=datetime.utcnow)

class ComplianceRecord(Base):
    __tablename__ = "compliance_records"

    id = Column(Integer, primary_key=True, index=True)

    intern_email = Column(String, index=True)
    report_date = Column(String)  # DD/MM/YY

    reminder_sent = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
