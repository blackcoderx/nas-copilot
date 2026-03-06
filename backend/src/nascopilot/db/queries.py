import json
from datetime import datetime
from uuid import UUID

import asyncpg


# ── Cases ─────────────────────────────────────────────────────────────────────

async def insert_case(conn: asyncpg.Connection, data: dict) -> dict:
    row = await conn.fetchrow(
        """
        INSERT INTO cases (
            incident_time, pickup, destination,
            pickup_lat, pickup_lon, dest_lat, dest_lon,
            patient_age, patient_sex,
            complaint, vitals, interventions, notes
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
        RETURNING *
        """,
        data["incident_time"], data["pickup"], data["destination"],
        data.get("pickup_lat"), data.get("pickup_lon"),
        data.get("dest_lat"), data.get("dest_lon"),
        data.get("patient_age"), data.get("patient_sex"),
        data["complaint"], data["vitals"],
        data.get("interventions"), data.get("notes"),
    )
    return dict(row)


async def get_case(conn: asyncpg.Connection, case_id: UUID) -> dict | None:
    row = await conn.fetchrow("SELECT * FROM cases WHERE id = $1", case_id)
    return dict(row) if row else None


async def list_cases(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch(
        "SELECT * FROM cases ORDER BY created_at DESC LIMIT 100"
    )
    return [dict(r) for r in rows]


async def finalize_case(conn: asyncpg.Connection, case_id: UUID) -> dict | None:
    row = await conn.fetchrow(
        """
        UPDATE cases SET status = 'FINAL', updated_at = NOW()
        WHERE id = $1 RETURNING *
        """,
        case_id,
    )
    return dict(row) if row else None


# ── Generations ───────────────────────────────────────────────────────────────

async def insert_generation(conn: asyncpg.Connection, data: dict) -> dict:
    row = await conn.fetchrow(
        """
        INSERT INTO generations (
            case_id, pcr_text, recommendation, model_name,
            facilities_json, route_json, weather_json
        ) VALUES ($1,$2,$3,$4,$5,$6,$7)
        RETURNING *
        """,
        data["case_id"],
        data["pcr_text"],
        data.get("recommendation"),
        data.get("model_name"),
        json.dumps(data.get("facilities_json")) if data.get("facilities_json") else None,
        json.dumps(data.get("route_json")) if data.get("route_json") else None,
        json.dumps(data.get("weather_json")) if data.get("weather_json") else None,
    )
    return dict(row)


async def get_latest_generation(conn: asyncpg.Connection, case_id: UUID) -> dict | None:
    row = await conn.fetchrow(
        "SELECT * FROM generations WHERE case_id = $1 ORDER BY created_at DESC LIMIT 1",
        case_id,
    )
    return dict(row) if row else None


async def get_all_generations(conn: asyncpg.Connection, case_id: UUID) -> list[dict]:
    rows = await conn.fetch(
        "SELECT * FROM generations WHERE case_id = $1 ORDER BY created_at DESC",
        case_id,
    )
    return [dict(r) for r in rows]


# ── Quality Flags ─────────────────────────────────────────────────────────────

async def insert_flags(conn: asyncpg.Connection, generation_id: UUID, flags: list[dict]) -> list[dict]:
    if not flags:
        return []
    rows = []
    for flag in flags:
        row = await conn.fetchrow(
            """
            INSERT INTO quality_flags (generation_id, severity, issue, action)
            VALUES ($1,$2,$3,$4) RETURNING *
            """,
            generation_id, flag["severity"], flag["issue"], flag["action"],
        )
        rows.append(dict(row))
    return rows


async def get_flags_for_generation(conn: asyncpg.Connection, generation_id: UUID) -> list[dict]:
    rows = await conn.fetch(
        "SELECT * FROM quality_flags WHERE generation_id = $1 ORDER BY severity",
        generation_id,
    )
    return [dict(r) for r in rows]
