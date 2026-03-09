import json
import secrets
from uuid import UUID

import asyncpg


# ── Cases ─────────────────────────────────────────────────────────────────────

async def insert_case(conn: asyncpg.Connection, data: dict, created_by: str | None = None) -> dict:
    def js(v):
        return json.dumps(v) if v else None

    outcome_token = secrets.token_urlsafe(16)
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
            interventions, notes, crew_names,
            created_by, outcome_token
        ) VALUES (
            $1,$2,$3,$4,$5,$6,
            $7,$8,$9,$10,$11,$12,
            $13,
            $14,$15,$16,$17,
            $18,$19,$20,
            $21,$22,$23,$24,$25,$26,
            $27,$28,
            $29,$30,$31,
            $32,$33
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
        created_by, outcome_token,
    )
    return dict(row)


async def get_case(
    conn: asyncpg.Connection,
    case_id: UUID,
    user_id: str | None = None,
    role: str = "emt",
    hospital_id: str | None = None,
) -> dict | None:
    if role == "superadmin":
        row = await conn.fetchrow("SELECT * FROM cases WHERE id = $1", case_id)
    elif role == "admin":
        row = await conn.fetchrow(
            """
            SELECT c.* FROM cases c
            WHERE c.id = $1
              AND (
                c.created_by IN (SELECT id FROM users WHERE hospital_id = $2)
                OR c.created_by IS NULL
              )
            """,
            case_id, hospital_id,
        )
    else:
        row = await conn.fetchrow(
            "SELECT * FROM cases WHERE id = $1 AND created_by = $2",
            case_id, user_id,
        )
    return dict(row) if row else None


async def list_cases(
    conn: asyncpg.Connection,
    user_id: str | None = None,
    role: str = "emt",
    hospital_id: str | None = None,
) -> list[dict]:
    if role == "superadmin":
        rows = await conn.fetch("SELECT * FROM cases ORDER BY created_at DESC LIMIT 200")
    elif role == "admin":
        rows = await conn.fetch(
            """
            SELECT c.* FROM cases c
            WHERE c.created_by IN (SELECT id FROM users WHERE hospital_id = $1)
               OR c.created_by IS NULL
            ORDER BY c.created_at DESC LIMIT 200
            """,
            hospital_id,
        )
    else:
        rows = await conn.fetch(
            "SELECT * FROM cases WHERE created_by = $1 ORDER BY created_at DESC LIMIT 100",
            user_id,
        )
    return [dict(r) for r in rows]


async def finalize_case(
    conn: asyncpg.Connection,
    case_id: UUID,
    user_id: str | None = None,
    role: str = "emt",
    hospital_id: str | None = None,
) -> dict | None:
    if role == "superadmin":
        where = "id = $1"
        params = [case_id]
    elif role == "admin":
        where = "id = $1 AND created_by IN (SELECT id FROM users WHERE hospital_id = $2)"
        params = [case_id, hospital_id]
    else:
        where = "id = $1 AND created_by = $2"
        params = [case_id, user_id]

    row = await conn.fetchrow(
        f"UPDATE cases SET status = 'FINAL', updated_at = NOW() WHERE {where} RETURNING *",
        *params,
    )
    return dict(row) if row else None


# ── Generations ───────────────────────────────────────────────────────────────

async def insert_generation(conn: asyncpg.Connection, data: dict) -> dict:
    row = await conn.fetchrow(
        """
        INSERT INTO generations (
            case_id, pcr_text, recommendation, model_name,
            facilities_json, route_json, weather_json, triage_json
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        RETURNING *
        """,
        data["case_id"], data["pcr_text"], data.get("recommendation"), data.get("model_name"),
        json.dumps(data.get("facilities_json")) if data.get("facilities_json") else None,
        json.dumps(data.get("route_json")) if data.get("route_json") else None,
        json.dumps(data.get("weather_json")) if data.get("weather_json") else None,
        json.dumps(data.get("triage_json")) if data.get("triage_json") else None,
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


# ── Outcomes ───────────────────────────────────────────────────────────────────

async def get_case_by_outcome_token(conn: asyncpg.Connection, token: str) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT c.id, c.complaint, c.patient_name, c.patient_age, c.patient_sex,
               c.pickup, c.destination, c.incident_time, c.status, c.outcome_token
        FROM cases c
        WHERE c.outcome_token = $1
        """,
        token,
    )
    return dict(row) if row else None


async def get_outcome_by_case(conn: asyncpg.Connection, case_id: UUID) -> dict | None:
    row = await conn.fetchrow(
        "SELECT * FROM outcomes WHERE case_id = $1",
        case_id,
    )
    return dict(row) if row else None


async def upsert_outcome(conn: asyncpg.Connection, case_id: UUID, data: dict) -> dict:
    row = await conn.fetchrow(
        """
        INSERT INTO outcomes (case_id, patient_status, admission_ward, confirmed_diagnosis, notes)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (case_id) DO UPDATE
          SET patient_status      = EXCLUDED.patient_status,
              admission_ward      = EXCLUDED.admission_ward,
              confirmed_diagnosis = EXCLUDED.confirmed_diagnosis,
              notes               = EXCLUDED.notes,
              submitted_at        = NOW()
        RETURNING *
        """,
        case_id,
        data["patient_status"],
        data.get("admission_ward"),
        data.get("confirmed_diagnosis"),
        data.get("notes"),
    )
    return dict(row)


# ── Facility Status ────────────────────────────────────────────────────────────

async def upsert_facility_status(conn: asyncpg.Connection, hospital_id: UUID, data: dict) -> dict:
    row = await conn.fetchrow(
        """
        INSERT INTO facility_status
            (hospital_id, icu_beds_available, surgical_theater, blood_bank, maternity, special_alert,
             updated_at, expires_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW() + INTERVAL '4 hours')
        ON CONFLICT (hospital_id) DO UPDATE
          SET icu_beds_available = EXCLUDED.icu_beds_available,
              surgical_theater   = EXCLUDED.surgical_theater,
              blood_bank         = EXCLUDED.blood_bank,
              maternity          = EXCLUDED.maternity,
              special_alert      = EXCLUDED.special_alert,
              updated_at         = NOW(),
              expires_at         = NOW() + INTERVAL '4 hours'
        RETURNING *
        """,
        hospital_id,
        data.get("icu_beds_available"),
        data.get("surgical_theater", "available"),
        data.get("blood_bank", "stocked"),
        data.get("maternity", "available"),
        data.get("special_alert"),
    )
    return dict(row)


async def get_facility_status(conn: asyncpg.Connection, hospital_id: UUID) -> dict | None:
    row = await conn.fetchrow(
        "SELECT fs.*, h.name AS hospital_name FROM facility_status fs JOIN hospitals h ON h.id = fs.hospital_id WHERE fs.hospital_id = $1",
        hospital_id,
    )
    return dict(row) if row else None


async def get_all_facility_statuses(conn: asyncpg.Connection) -> list[dict]:
    rows = await conn.fetch(
        """
        SELECT fs.*, h.name AS hospital_name
        FROM facility_status fs
        JOIN hospitals h ON h.id = fs.hospital_id
        ORDER BY h.name
        """,
    )
    return [dict(r) for r in rows]
