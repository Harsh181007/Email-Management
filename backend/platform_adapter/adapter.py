from datetime import datetime
from collections import defaultdict

from backend.core.database import SessionLocal
from backend.domain.models import WorkUpdate
from backend.services.risk.risk import compute_risk
from backend.platform_adapter.schemas import PlatformSnapshot, InternStatus


def get_platform_snapshot() -> PlatformSnapshot:
    """
    Canonical snapshot exposed for internal platform integration.
    """
    db = SessionLocal()
    updates = db.query(WorkUpdate).all()
    db.close()

    grouped = defaultdict(list)
    for u in updates:
        grouped[u.intern_id].append(u)

    interns = []

    for intern_id, ups in grouped.items():
        latest = max(ups, key=lambda x: x.created_at)
        risk = compute_risk(ups)

        interns.append(
            InternStatus(
                intern_id=intern_id,
                project=latest.project,
                status=latest.status,
                risk=risk,
                last_updated=latest.created_at
            )
        )

    return PlatformSnapshot(
        generated_at=datetime.utcnow(),
        interns=interns
    )
