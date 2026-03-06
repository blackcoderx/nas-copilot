from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CaseCreate(BaseModel):
    incident_time: datetime
    pickup: str
    destination: str
    pickup_lat: float | None = None
    pickup_lon: float | None = None
    dest_lat: float | None = None
    dest_lon: float | None = None
    patient_age: int | None = None
    patient_sex: str | None = None
    complaint: str
    vitals: str
    interventions: str | None = None
    notes: str | None = None


class CaseOut(BaseModel):
    id: UUID
    incident_time: datetime
    pickup: str
    destination: str
    pickup_lat: float | None
    pickup_lon: float | None
    dest_lat: float | None
    dest_lon: float | None
    patient_age: int | None
    patient_sex: str | None
    complaint: str
    vitals: str
    interventions: str | None
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class CaseListItem(BaseModel):
    id: UUID
    complaint: str
    pickup: str
    destination: str
    status: str
    created_at: datetime
