from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from nascopilot.database import get_conn
from nascopilot.db import queries
from nascopilot.dependencies import get_current_user
from nascopilot.models.facility import FacilityStatusUpdate, FacilityStatusOut

router = APIRouter(prefix="/facilities", tags=["facilities"])


def _to_out(row: dict) -> FacilityStatusOut:
    is_expired = row["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc)
    return FacilityStatusOut(**row, is_expired=is_expired)


@router.get("/status", response_model=list[FacilityStatusOut])
async def list_facility_statuses():
    """Public — returns live capacity status for all hospitals.
    EMTs use this when selecting a destination facility."""
    async with get_conn() as conn:
        rows = await queries.get_all_facility_statuses(conn)
    return [_to_out(r) for r in rows]


@router.put("/status", response_model=FacilityStatusOut)
async def update_facility_status(body: FacilityStatusUpdate, user: dict = Depends(get_current_user)):
    """Admin-only — update the capacity status for the admin's own hospital.
    Status automatically expires after 4 hours to prevent stale data."""
    if user["role"] not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Only hospital admins can update facility status")
    hospital_id = user.get("hospital_id")
    if not hospital_id:
        raise HTTPException(status_code=400, detail="Your account is not linked to a hospital")

    async with get_conn() as conn:
        row = await queries.upsert_facility_status(conn, hospital_id, body.model_dump())
    return _to_out(row)
