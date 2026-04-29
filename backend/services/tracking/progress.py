from backend.core.database import SessionLocal
from backend.domain.models import WorkUpdate


def get_intern_progress(intern_email: str):
    """
    Returns the chronological progress of one intern.
    """
    db = SessionLocal()

    records = (
        db.query(WorkUpdate)
        .filter(WorkUpdate.intern_id == intern_email)
        .order_by(WorkUpdate.created_at.asc())
        .all()
    )

    progress = [
        {
            "date": r.created_at,
            "project": r.project,
            "summary": r.summary,
            "status": r.status
        }
        for r in records
    ]

    db.close()
    return progress
