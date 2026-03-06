from uuid import UUID

from pydantic import BaseModel


class QualityFlag(BaseModel):
    id: UUID
    generation_id: UUID
    severity: str  # high | medium | low
    issue: str
    action: str
