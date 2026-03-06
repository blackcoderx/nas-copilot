import json
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from nascopilot.database import get_conn
from nascopilot.db import queries
from nascopilot.models.case import CaseCreate, CaseOut, CaseListItem
from nascopilot.models.generation import GenerationOut
from nascopilot.models.flag import QualityFlag
from nascopilot.services.generate import run_generate

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseOut, status_code=201)
async def create_case(body: CaseCreate):
    async with get_conn() as conn:
        row = await queries.insert_case(conn, body.model_dump())
    return CaseOut(**row)


@router.get("", response_model=list[CaseListItem])
async def list_cases():
    async with get_conn() as conn:
        rows = await queries.list_cases(conn)
    return [CaseListItem(**r) for r in rows]


@router.get("/{case_id}")
async def get_case(case_id: UUID):
    async with get_conn() as conn:
        case_row = await queries.get_case(conn, case_id)
        if not case_row:
            raise HTTPException(status_code=404, detail="Case not found")
        gen_row = await queries.get_latest_generation(conn, case_id)
        flags = []
        if gen_row:
            flag_rows = await queries.get_flags_for_generation(conn, gen_row["id"])
            flags = [QualityFlag(**f) for f in flag_rows]

    case_out = CaseOut(**case_row)
    gen_out = None
    if gen_row:
        gen_out = GenerationOut(**gen_row, flags=flags)

    return {"case": case_out.model_dump(mode="json"), "latest_generation": gen_out.model_dump(mode="json") if gen_out else None}


@router.post("/{case_id}/generate", response_model=GenerationOut)
async def generate(case_id: UUID):
    try:
        async with get_conn() as conn:
            result = await run_generate(conn, case_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Generation failed: {exc}")
    return result


@router.patch("/{case_id}/finalize", response_model=CaseOut)
async def finalize(case_id: UUID):
    async with get_conn() as conn:
        row = await queries.finalize_case(conn, case_id)
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseOut(**row)


@router.get("/{case_id}/export")
async def export_case(case_id: UUID):
    async with get_conn() as conn:
        case_row = await queries.get_case(conn, case_id)
        if not case_row:
            raise HTTPException(status_code=404, detail="Case not found")
        gen_rows = await queries.get_all_generations(conn, case_id)
        generations = []
        for gen in gen_rows:
            flag_rows = await queries.get_flags_for_generation(conn, gen["id"])
            generations.append({**gen, "flags": flag_rows})

    def _serial(obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        if hasattr(obj, "__str__"):
            return str(obj)
        raise TypeError(f"Not serializable: {type(obj)}")

    payload = {"case": case_row, "generations": generations}
    return JSONResponse(
        content=json.loads(json.dumps(payload, default=_serial)),
        headers={"Content-Disposition": f'attachment; filename="case-{case_id}.json"'},
    )
