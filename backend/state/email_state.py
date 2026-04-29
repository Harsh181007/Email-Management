import os

STATE_FILE = "last_uid.txt"


def get_last_uid():
    """
    Returns the last processed UID.
    If the state file doesn't exist, return 0.
    """
    if not os.path.exists(STATE_FILE):
        return 0

    try:
        with open(STATE_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0


def set_last_uid(uid: int):
    """
    Stores the latest processed UID.
    """
    with open(STATE_FILE, "w") as f:
        f.write(str(uid))