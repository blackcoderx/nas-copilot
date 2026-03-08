import asyncio
from uuid import UUID

import asyncpg

from nascopilot.config import settings
from nascopilot.db import queries
from nascopilot.models.generation import GenerationOut
from nascopilot.models.flag import QualityFlag
from nascopilot.services.ai import build_prompt, call_ollama, deterministic_flags
from nascopilot.services.overpass import get_nearby_facilities
from nascopilot.services.openroute import get_route_eta
from nascopilot.services.weather import get_weather


async def run_generate(conn: asyncpg.Connection, case_id: UUID) -> GenerationOut:
    case = await queries.get_case(conn, case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found")

    # Fetch external context concurrently; failures are swallowed per-service
    facilities_task = None
    route_task = None
    weather_task = None

    p_lat = case.get("pickup_lat")
    p_lon = case.get("pickup_lon")
    d_lat = case.get("dest_lat")
    d_lon = case.get("dest_lon")

    tasks = []
    if p_lat and p_lon:
        tasks.append(get_nearby_facilities(p_lat, p_lon))
    else:
        tasks.append(_noop([]))

    if p_lat and p_lon and d_lat and d_lon:
        tasks.append(get_route_eta(p_lat, p_lon, d_lat, d_lon))
    else:
        tasks.append(_noop(None))

    tasks.append(get_weather(p_lat, p_lon, d_lat, d_lon))

    facilities, route, weather = await asyncio.gather(*tasks)

    context = {"facilities": facilities, "route": route, "weather": weather}

    system_msg, user_msg = build_prompt(case, context)
    ai_result = await call_ollama(system_msg, user_msg)

    pcr_text = ai_result.get("pcr_text", "")
    recommendation = ai_result.get("recommendation")

    # Merge deterministic rule-based flags with AI-generated flags
    # Deduplicate by issue text so the same gap isn't flagged twice
    det_flags = deterministic_flags(case)
    ai_flags  = ai_result.get("flags", [])
    det_issues = {f["issue"] for f in det_flags}
    merged = det_flags + [f for f in ai_flags if f.get("issue") not in det_issues]
    raw_flags = merged

    gen_data = {
        "case_id": case_id,
        "pcr_text": pcr_text,
        "recommendation": recommendation,
        "model_name": settings.ollama_model,
        "facilities_json": facilities or None,
        "route_json": route or None,
        "weather_json": weather or None,
    }
    gen_row = await queries.insert_generation(conn, gen_data)
    gen_id = gen_row["id"]

    flag_rows = await queries.insert_flags(conn, gen_id, raw_flags)

    return GenerationOut(
        **gen_row,
        flags=[QualityFlag(**f) for f in flag_rows],
    )


async def _noop(value):
    return value
