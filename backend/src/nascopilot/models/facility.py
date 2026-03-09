from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FacilityStatusUpdate(BaseModel):
    icu_beds_available: int | None = None
    surgical_theater: str = "available"    # available | occupied | emergency_only
    blood_bank: str = "stocked"            # stocked | low | out
    maternity: str = "available"           # available | full
    special_alert: str | None = None


class FacilityStatusOut(BaseModel):
    id: UUID
    hospital_id: UUID
    hospital_name: str | None = None
    icu_beds_available: int | None
    surgical_theater: str
    blood_bank: str
    maternity: str
    special_alert: str | None
    updated_at: datetime
    expires_at: datetime
    is_expired: bool = False
