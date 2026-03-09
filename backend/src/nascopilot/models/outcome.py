from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OutcomeSubmit(BaseModel):
    patient_status: str       # admitted | discharged | deceased | transferred
    admission_ward: str | None = None
    confirmed_diagnosis: str | None = None
    notes: str | None = None


class OutcomeOut(BaseModel):
    id: UUID
    case_id: UUID
    patient_status: str
    admission_ward: str | None
    confirmed_diagnosis: str | None
    notes: str | None
    submitted_at: datetime
