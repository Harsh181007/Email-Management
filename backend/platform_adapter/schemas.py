from pydantic import BaseModel
from typing import List
from datetime import datetime

class InternStatus(BaseModel):
    intern_id: int
    project: str
    status: str
    risk: str
    last_updated: datetime


class PlatformSnapshot(BaseModel):
    generated_at: datetime
    interns: List[InternStatus]
