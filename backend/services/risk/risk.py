from datetime import datetime, timedelta

def compute_risk(updates):
    """
    updates: list[WorkUpdate] for a single intern
    """
    if not updates:
        return "NO_DATA"

    latest = max(updates, key=lambda u: u.created_at)
    now = datetime.utcnow()

    # Blocked always highest priority
    if latest.status == "BLOCKED":
        return "BLOCKED"

    # No updates
    if now - latest.created_at > timedelta(hours=48):
        return "INACTIVE"

    # Stagnant progress
    statuses = [u.status for u in updates[-3:]]
    if len(set(statuses)) == 1:
        return "STAGNANT"

    # ETA breach
    if latest.eta and now > latest.eta:
        return "DELAYED"

    return "ON_TRACK"
