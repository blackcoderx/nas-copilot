import json

import httpx

from nascopilot.config import settings


def _vitals_line(v: dict | None, label: str) -> str:
    if not v:
        return f"{label}: Not documented"
    parts = []
    if v.get("bp_sys") and v.get("bp_dia"):
        parts.append(f"BP {v['bp_sys']}/{v['bp_dia']} mmHg")
    if v.get("hr"):
        parts.append(f"HR {v['hr']} bpm")
    if v.get("rr"):
        parts.append(f"RR {v['rr']} /min")
    if v.get("spo2") is not None:
        parts.append(f"SpO\u2082 {v['spo2']}%")
    if v.get("gcs") is not None:
        parts.append(f"GCS {v['gcs']}/15")
    if v.get("pain") is not None:
        parts.append(f"Pain {v['pain']}/10")
    if v.get("temp_c") is not None:
        parts.append(f"Temp {v['temp_c']}\u00b0C")
    t = v.get("time")
    time_str = f" [{t}]" if t else ""
    return f"{label}{time_str}: {', '.join(parts) if parts else 'Values not recorded'}"


def build_prompt(case: dict, context: dict) -> tuple[str, str]:
    route      = context.get("route") or {}
    weather    = context.get("weather") or {}
    facilities = context.get("facilities") or []

    route_text = (
        f"{route['distance_km']} km / {route['duration_min']} min drive"
        if route else "Route data unavailable"
    )

    def wx_text(wx: dict | None) -> str:
        if not wx:
            return "Unavailable"
        return f"{wx.get('condition','?')}, {wx.get('temperature_c','?')}\u00b0C, wind {wx.get('wind_kmh','?')} km/h"

    facility_lines = "\n".join(
        f"  - {f['name']} ({f['type']})" for f in facilities
    ) or "  None found nearby"

    def _parse_vitals(raw):
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return None
        return raw

    v1 = _parse_vitals(case.get("vitals_set_1"))
    v2 = _parse_vitals(case.get("vitals_set_2"))

    vitals_block = (
        _vitals_line(v1, "Vitals Set 1 (on-scene/pickup)") + "\n" +
        _vitals_line(v2, "Vitals Set 2 (en-route/arrival)")
    )

    def t(key):
        return case.get(key) or "Not recorded"

    system_msg = (
        "You are a clinical documentation assistant for Ghana's National Ambulance Service (NAS). "
        "NAS operates primarily as an inter-facility transfer (IFT) service — moving patients between "
        "CHPS compounds, district hospitals, regional hospitals, and teaching hospitals. "
        "Common presentations include: malaria (including cerebral malaria), obstetric emergencies "
        "(eclampsia, PPH, obstructed labour), road traffic accidents, hypertensive emergencies, "
        "diabetic emergencies, stroke, sepsis, and snake or scorpion envenomation. "
        "Your PCR narrative must reflect the IFT context: reference the sending facility's diagnosis, "
        "the patient's condition at pickup, changes en route, and condition at handoff. "
        "Use clinical EMS language. Write in past tense, third person. "
        "If any data field is missing, write 'not documented' — never fabricate values. "
        "Respond with ONLY valid JSON. No markdown fences, no text outside the JSON. "
        'Schema: {"pcr_text":"...","recommendation":"...","flags":['
        '{"severity":"high|medium|low","issue":"...","action":"..."}]}'
    )

    user_msg = f"""=== INCIDENT DETAILS ===
Dispatch time:       {t('dispatch_time')}
Incident time:       {t('incident_time')}
On-scene time:       {t('on_scene_time')}
Transport start:     {t('transport_start')}
Arrival at dest:     {t('arrival_time')}
Transfer of care:    {t('transfer_care_time')}
Transport mode:      {case.get('transport_mode', 'non-emergent').upper()}

=== INTER-FACILITY TRANSFER ===
Sending facility:    {case.get('pickup', 'Not documented')}
Sending physician:   {case.get('sending_physician') or 'Not documented'}
Sending diagnosis:   {case.get('sending_diagnosis') or 'Not documented'}
Reason for transfer: {case.get('referral_reason') or 'Not documented'}
Destination:         {case.get('destination', 'Not documented')}
Receiving provider:  {case.get('receiving_provider') or 'Not documented'}

=== PATIENT ===
Name:                {case.get('patient_name') or 'Not documented'}
Age:                 {case.get('patient_age') or 'Not documented'}
Sex:                 {case.get('patient_sex') or 'Not documented'}

=== SAMPLE HISTORY ===
Chief complaint:     {case.get('complaint', 'Not documented')}
Allergies:           {case.get('allergies') or 'Not documented'}
Medications:         {case.get('current_medications') or 'Not documented'}
Past medical hx:     {case.get('past_medical_hx') or 'Not documented'}
Last oral intake:    {case.get('last_oral_intake') or 'Not documented'}
Events leading:      {case.get('events_leading') or 'Not documented'}

=== VITAL SIGNS ===
{vitals_block}

=== INTERVENTIONS & CREW ===
Interventions: {case.get('interventions') or 'None documented'}
Crew:          {case.get('crew_names') or 'Not documented'}
Notes:         {case.get('notes') or 'None'}

=== OPERATIONAL CONTEXT ===
Route to destination: {route_text}
Weather at pickup:    {wx_text(weather.get('pickup'))}
Weather at dest:      {wx_text(weather.get('destination'))}
Nearby facilities:
{facility_lines}

Write a complete NAS PCR narrative with these exact sections:
CHIEF COMPLAINT | DISPATCH & RESPONSE | PICKUP ASSESSMENT | HISTORY (SAMPLE) | VITAL SIGNS | INTERVENTIONS & PATIENT RESPONSE | TRANSPORT | HANDOFF NOTES

Then list all documentation quality flags.
Give a transfer recommendation appropriate to Ghana's facility hierarchy \
(CHPS compound → District Hospital → Regional Hospital → Teaching Hospital)."""

    return system_msg, user_msg


def deterministic_flags(case: dict) -> list[dict]:
    """Rule-based flags that always fire regardless of AI output."""
    flags: list[dict] = []

    def _parse(raw):
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except Exception:
                return None
        return raw

    v1 = _parse(case.get("vitals_set_1"))
    v2 = _parse(case.get("vitals_set_2"))

    # HIGH severity
    if not v1:
        flags.append({
            "severity": "high",
            "issue": "No vital signs documented",
            "action": "Document at least two timestamped vital sign sets (BP, HR, RR, SpO\u2082, GCS).",
        })
    elif not v2:
        flags.append({
            "severity": "high",
            "issue": "Only one set of vital signs recorded",
            "action": "NAS standard requires a minimum of two timestamped vital sign sets per transport.",
        })

    if v1 and v1.get("gcs") is None:
        flags.append({
            "severity": "high",
            "issue": "GCS not documented",
            "action": "Document Glasgow Coma Scale score on all patients. Critical for neurological status.",
        })

    if not case.get("allergies"):
        flags.append({
            "severity": "high",
            "issue": "Allergies not documented",
            "action": "Document patient allergies or record 'NKDA' (No Known Drug Allergies).",
        })

    if not case.get("sending_diagnosis") and not case.get("referral_reason"):
        flags.append({
            "severity": "high",
            "issue": "No sending diagnosis or referral reason documented",
            "action": "Document the sending facility's working diagnosis and reason for transfer.",
        })

    # MEDIUM severity
    if not case.get("sending_physician"):
        flags.append({
            "severity": "medium",
            "issue": "Sending physician not documented",
            "action": "Record the name of the physician who initiated the transfer.",
        })

    if not case.get("receiving_provider"):
        flags.append({
            "severity": "medium",
            "issue": "Receiving provider not documented",
            "action": "Record the name and role of the provider who accepted care at the destination.",
        })

    if not case.get("current_medications"):
        flags.append({
            "severity": "medium",
            "issue": "Current medications not documented",
            "action": "Document current medications or record 'None known'.",
        })

    if not case.get("interventions"):
        flags.append({
            "severity": "medium",
            "issue": "No interventions documented",
            "action": "Confirm no interventions were performed, or document all treatments given.",
        })

    if v1 and v1.get("pain") is None:
        flags.append({
            "severity": "medium",
            "issue": "Pain scale not documented",
            "action": "Assess and document pain (0-10 scale) for all conscious patients.",
        })

    # LOW severity
    if not case.get("patient_name"):
        flags.append({
            "severity": "low",
            "issue": "Patient name not documented",
            "action": "Record patient full name. Document 'Unknown' if unable to obtain.",
        })

    if not case.get("crew_names"):
        flags.append({
            "severity": "low",
            "issue": "Crew names not documented",
            "action": "Record the names and certification levels of all NAS crew on this transport.",
        })

    if not case.get("last_oral_intake"):
        flags.append({
            "severity": "low",
            "issue": "Last oral intake not documented",
            "action": "Document last oral intake — important for surgical and anaesthetic planning.",
        })

    return flags


async def call_ollama(system_msg: str, user_msg: str) -> dict:
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg},
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

    content = resp.json()["message"]["content"].strip()
    if content.startswith("```"):
        lines = content.splitlines()
        content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(content)
