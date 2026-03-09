from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from nascopilot.database import get_conn
from nascopilot.db import queries
from nascopilot.dependencies import get_current_user
from nascopilot.models.outcome import OutcomeSubmit, OutcomeOut

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


@router.get("/{token}")
async def get_outcome_page_data(token: str):
    """Public endpoint — returns case summary and existing outcome for the given token.
    Used by hospital staff to see what case they are submitting an outcome for."""
    async with get_conn() as conn:
        case = await queries.get_case_by_outcome_token(conn, token)
    if not case:
        raise HTTPException(status_code=404, detail="Outcome link not found or expired")
    outcome = None
    async with get_conn() as conn:
        outcome_row = await queries.get_outcome_by_case(conn, case["id"])
    if outcome_row:
        outcome = OutcomeOut(**outcome_row).model_dump(mode="json")
    return {"case": case, "outcome": outcome}


@router.post("/{token}", response_model=OutcomeOut)
async def submit_outcome(token: str, body: OutcomeSubmit):
    """Public endpoint — hospital staff submit patient outcome via the shared link.
    No authentication required; the unique token acts as the access credential."""
    valid_statuses = {"admitted", "discharged", "deceased", "transferred"}
    if body.patient_status not in valid_statuses:
        raise HTTPException(status_code=422, detail=f"patient_status must be one of: {', '.join(valid_statuses)}")

    async with get_conn() as conn:
        case = await queries.get_case_by_outcome_token(conn, token)
        if not case:
            raise HTTPException(status_code=404, detail="Outcome link not found")
        row = await queries.upsert_outcome(conn, case["id"], body.model_dump())
    return OutcomeOut(**row)


@router.get("/by-case/{case_id}", response_model=OutcomeOut)
async def get_outcome_for_case(case_id: UUID, user: dict = Depends(get_current_user)):
    """Authenticated — EMT/admin fetches the outcome for their own case."""
    async with get_conn() as conn:
        row = await queries.get_outcome_by_case(conn, case_id)
    if not row:
        raise HTTPException(status_code=404, detail="No outcome submitted yet")
    return OutcomeOut(**row)
