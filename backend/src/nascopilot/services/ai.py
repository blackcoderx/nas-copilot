import json

import httpx

from nascopilot.config import settings


def build_prompt(case: dict, context: dict) -> tuple[str, str]:
    route = context.get("route") or {}
    weather = context.get("weather") or {}
    facilities = context.get("facilities") or []

    route_text = (
        f"{route['distance_km']} km / {route['duration_min']} min drive"
        if route else "Route data unavailable"
    )

    def wx_text(wx: dict | None) -> str:
        if not wx:
            return "Unavailable"
        return f"{wx.get('condition', '?')}, {wx.get('temperature_c', '?')}°C, wind {wx.get('wind_kmh', '?')} km/h"

    pickup_wx = wx_text(weather.get("pickup"))
    dest_wx = wx_text(weather.get("destination"))

    facility_lines = "\n".join(
        f"- {f['name']} ({f['type']})" for f in facilities
    ) or "None found nearby"

    interventions = case.get("interventions") or "None documented"

    system_msg = (
        "You are an EMS clinical documentation assistant for Ghana's National Ambulance Service. "
        "Your job: produce a structured PCR narrative, quality flags, and a transfer recommendation. "
        "Always respond with ONLY valid JSON. No markdown, no explanations. "
        'Schema: {"pcr_text":"...","recommendation":"...","flags":[{"severity":"high|medium|low","issue":"...","action":"..."}]}'
    )

    user_msg = f"""=== CASE DATA ===
Incident time: {case.get('incident_time')}
Pickup facility: {case.get('pickup')}
Destination facility: {case.get('destination')}
Patient: {case.get('patient_age', '?')}y {case.get('patient_sex', '?')}
Chief complaint: {case.get('complaint')}
Vitals: {case.get('vitals')}
Interventions: {interventions}
Notes: {case.get('notes') or 'None'}

=== OPERATIONAL CONTEXT ===
Route to destination: {route_text}
Weather at pickup: {pickup_wx}
Weather at destination: {dest_wx}
Nearby health facilities (top 5):
{facility_lines}

Produce the PCR narrative in clear clinical language with sections: Chief Complaint, Assessment, Vitals, Interventions, Transport, Handoff Notes.
List all documentation quality flags you identify.
Give a brief, practical transfer recommendation."""

    return system_msg, user_msg


async def call_ollama(system_msg: str, user_msg: str) -> dict:
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
    }
    headers = {}
    if settings.ollama_api_key:
        headers["Authorization"] = f"Bearer {settings.ollama_api_key}"

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/chat", json=payload, headers=headers
        )
        resp.raise_for_status()

    content = resp.json()["message"]["content"]

    # Strip markdown code fences if model wraps JSON in them
    content = content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(content)
