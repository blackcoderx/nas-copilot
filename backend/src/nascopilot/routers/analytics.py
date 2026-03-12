from fastapi import APIRouter, Depends

from nascopilot.database import get_conn
from nascopilot.db import queries
from nascopilot.dependencies import require_admin

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def get_analytics_summary(user: dict = Depends(require_admin)):
    """Admin/Superadmin — aggregate analytics data for the dashboard."""
    role = user["role"]
    hospital_id = user.get("hospital_id")

    async with get_conn() as conn:
        cases_by_day, triage_dist, top_complaints, top_qa_flags, pcr_completion, locations, transport_split, outcomes_summary = await _gather(
            conn, role, hospital_id
        )

    return {
        "cases_by_day": cases_by_day,
        "triage_distribution": triage_dist,
        "top_complaints": top_complaints,
        "top_qa_flags": top_qa_flags,
        "pcr_completion": pcr_completion,
        "locations": locations,
        "transport_mode_split": transport_split,
        "outcomes_summary": outcomes_summary,
    }


async def _gather(conn, role: str, hospital_id: str | None) -> tuple:
    import asyncio
    return await asyncio.gather(
        queries.get_cases_by_day(conn, role, hospital_id),
        queries.get_triage_distribution(conn, role, hospital_id),
        queries.get_top_complaints(conn, role, hospital_id),
        queries.get_top_qa_flags(conn, role, hospital_id),
        queries.get_pcr_completion(conn, role, hospital_id),
        queries.get_case_locations(conn, role, hospital_id),
        queries.get_transport_mode_split(conn, role, hospital_id),
        queries.get_outcomes_summary(conn, role, hospital_id),
    )
