import json
from uuid import UUID

import asyncpg


# ── Cases ─────────────────────────────────────────────────────────────────────

async def insert_case(conn: asyncpg.Connection, data: dict) -> dict:
    def js(v):
        return json.dumps(v) if v else None

    row = await conn.fetchrow(
        """
        INSERT INTO cases (
            dispatch_time, incident_time, on_scene_time, transport_start,
            arrival_time, transfer_care_time,
            pickup, destination, pickup_lat, pickup_lon, dest_lat, dest_lon,
            transport_mode,
            sending_physician, sending_diagnosis, referral_reason, receiving_provider,
            patient_name, patient_age, patient_sex,
            complaint, allergies, current_medications, past_medical_hx,
            last_oral_intake, events_leading,
            vitals_set_1, vitals_set_2,
            interventions, notes, crew_names
        ) VALUES (
            $1,$2,$3,$4,$5,$6,
            $7,$8,$9,$10,$11,$12,
            $13,
            $14,$15,$16,$17,
            $18,$19,$20,
            $21,$22,$23,$24,$25,$26,
            $27,$28,
            $29,$30,$31
        )
        RETURNING *
        """,
        data.get("dispatch_time"), data["incident_time"], data.get("on_scene_time"),
        data.get("transport_start"), data.get("arrival_time"), data.get("transfer_care_time"),
        data["pickup"], data["destination"],
        data.get("pickup_lat"), data.get("pickup_lon"),
        data.get("dest_lat"), data.get("dest_lon"),
        data.get("transport_mode", "non-emergent"),
        data.get("sending_physician"), data.get("sending_diagnosis"),
        data.get("referral_reason"), data.get("receiving_provider"),
        data.get("patient_name"), data.get("patient_age"), data.get("patient_sex"),
        data["complaint"],
        data.get("allergies"), data.get("current_medications"),
        data.get("past_medical_hx"), data.get("last_oral_intake"), data.get("events_leading"),
        js(data.get("vitals_set_1")), js(data.get("vitals_set_2")),
        data.get("interventions"), data.get("notes"), data.get("crew_names"),
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
        "UPDATE cases SET status = 'FINAL', updated_at = NOW() WHERE id = $1 RETURNING *",
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
        data["case_id"], data["pcr_text"], data.get("recommendation"), data.get("model_name"),
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
            "INSERT INTO quality_flags (generation_id, severity, issue, action) VALUES ($1,$2,$3,$4) RETURNING *",
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
