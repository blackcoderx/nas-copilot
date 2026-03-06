## NAS Copilot GH (text-only) — detailed idea brief for your agent

### 1) The pitch
Build a simple web app that helps Ghana EMS teams **type a patient case once** and instantly get a **clean Patient Care Report (PCR)** plus a **quality checklist (missing/risky documentation)** and an **operational recommendation** (nearest facilities + route ETA + weather).  

### 2) The real problem (in plain terms)
EMTs are busy and stressed, so documentation is often:
- **Incomplete** (missing allergies, pain score, timelines, vitals reassessment, etc.)
- **Inconsistent** (different formats, hard to read, hard to audit)
- **Hard to review** (QA teams can’t realistically review 100% fast)
- **Hard to learn from** (leadership can’t reliably aggregate messy free-text into system metrics)

In the US, this gets framed as “billing optimization.” In Ghana NAS (often free service), the value shifts to **quality + accountability + operations + data for funding justification**.

### 3) What the app does (core features)
1) **Case capture (text-only):** EMT types incident + patient details into a structured form.  
2) **PCR generation:** AI turns those fields into a properly formatted narrative PCR (still editable).  
3) **Quality flags:** AI highlights missing or concerning documentation and tells the EMT what to add.  
4) **Ops context (optional but strong):**
   - “What facilities are nearby?” (OSM/Overpass)
   - “How long will it take?” (OpenRouteService ETA)
   - “Will weather slow this down?” (Open‑Meteo)
5) **History + accountability:** Every generation is saved so you can show “before/after” and prove improvements over time.

### 4) How users actually use it (workflow)
- **Create case → Save** (so nothing is lost)
- **Generate** (AI produces PCR + flags + recommendation)
- **Fix missing items** (EMT adds allergies/pain score/etc.)
- **Regenerate** (cleaner PCR, fewer flags)
- **Finalize + export** (copy text / download JSON for records)

### 5) How the system works behind the scenes (stack responsibilities)
- **Astro (frontend):** fast pages + forms + results UI; file-based pages make it easy to build “New Case / Case List / Case Detail” screens.   
- **FastAPI (backend):** the “brain” of the product:
  - validates inputs, controls the workflow, calls external APIs, calls the LLM, and writes to the DB
  - handles CORS so the browser UI can call it safely.   
- **Neon (DB):** Postgres storage for cases, generations, and QA flags; Neon connections commonly require SSL mode “Require” in connection settings.   
- **Ollama Cloud model (LLM):** backend calls the Ollama API to produce structured results (PCR + flags + recommendation). Ollama’s API docs describe chat-style endpoints for this workflow.   

### 6) What must be stored in the DB (so it counts as “real” software)
Store three layers:
- **Case (what EMT typed):** complaint, vitals, notes, pickup/destination, coordinates, interventions.
- **Generation (each AI run):** the PCR output, recommendation text, model name, timestamp, and “context snapshots” (route/weather/facilities) used to generate.
- **Quality flags (rows):** severity + issue + action, linked to a specific generation.
This makes the app auditable, demo-friendly (“regenerate history”), and useful for analytics.

---

## Example: what the input form looks like (with sample values)
Incident (typed):
- Incident time: 2026‑03‑06 14:32 GMT  
- Pickup facility: Tamale Teaching Hospital  
- Destination facility: Korle Bu Teaching Hospital (Accra)  
- Latitude / Longitude: 9.407 / -0.853  

Patient & care (typed):
- Approx age: 45  
- Sex: Male  
- Chief complaint: Severe abdominal pain  
- Vitals: BP 90/60, HR 112, RR 24, SpO₂ 94  
- Interventions (text lines): “IV access”, “500ml normal saline bolus”  
- Notes: “Suspected bowel obstruction; patient looks unwell.”

---

## Example: what the AI output should look like (human-readable + structured)
PCR draft (text block):
- Clear headings: Chief complaint, assessment, vitals, interventions, transport, handoff notes  
- Clean, consistent language suitable for printing/copying  

Quality flags (list):
- High: “Allergies not documented → Ask patient/family; record ‘Unknown’ if not available.”
- Medium: “Pain score missing → record 0–10; reassess after intervention.”
- Medium: “Low BP + high HR → possible shock risk; recheck vitals every 15 minutes.”

Transfer recommendation (short, practical):
- “Given instability + long ETA, consider closer surgical-capable facility first; stabilize before long transfer when possible; monitoring reminders.”

Ops snapshot (if enabled):
- Route: distance + ETA to destination (and optionally to top alternatives)
- Weather: pickup + destination current conditions
- Nearby facilities: top 5 hospitals/clinics by distance

---

### 7) Non-goals (to keep it hackathon-simple)
- No voice input, no speech-to-text
- No automatic EHR integration
- No “AI makes final medical decisions” claim (it’s decision support + documentation helper)

### 8) One-sentence definition of done (for planning)
A user can **type a case**, **save it to Neon**, press **Generate**, and see a **saved, reloadable PCR + QA flags + recommendation** on the case page, with optional route/weather/facility context.


## APIs we’ll use (and exactly how we’ll use them)

### 1) Internal API (Astro → FastAPI) — “your app’s own endpoints”
**What it’s for:** The frontend never talks to the DB or AI directly. It calls FastAPI over HTTPS/HTTP with JSON.  
**How we’ll use it:**
- **Create a case:** user submits the text form → FastAPI stores it in Neon.
- **List cases:** frontend fetches saved cases for a “Case History” page.
- **Generate output:** frontend triggers “Generate PCR + QA” → FastAPI orchestrates external APIs + LLM, saves results, returns them.
- **Finalize + export:** mark a case as FINAL; download a JSON/text export for the demo.

---

### 2) Neon (Postgres) — database connection (not a “web API,” but still a key integration)
**What it’s for:** Persistent storage (the hackathon DB requirement) so your demo survives refresh and you can show history.  
**How we’ll use it:**
- Store **cases** (the typed inputs).
- Store **generations** (each AI run, including PCR text and a timestamp).
- Store **quality flags** (rows, so you can later aggregate “top documentation gaps”).
- Store **context snapshots** (route/weather/facilities) to make results replayable.  
**Important constraint:** Neon requires SSL/TLS for connections and recommends specifying `sslmode=require` in the connection string. 

---

### 3) Ollama API (Cloud model) — AI generation
**What it’s for:** Turn typed inputs + context into structured output:
- PCR draft (clean narrative)
- QA flags (missing/risky documentation)
- Transfer recommendation (short, practical guidance)  
**How we’ll use it:**
- FastAPI calls the Ollama **chat** endpoint (`/api/chat`) with:
  - the case data (complaint, vitals, interventions, notes)
  - optional ops context (route/weather/facilities)
- We instruct the model to return **structured JSON** so the UI can reliably render cards (PCR / flags / ops). 

---

### 4) Overpass API (OpenStreetMap) — nearby hospitals/clinics
**What it’s for:** Given a latitude/longitude, find **nearby health facilities** (hospital/clinic) without needing a paid maps product.  
**How we’ll use it:**
- FastAPI calls the Overpass “interpreter” endpoint and asks for OSM objects tagged like:
  - `amenity=hospital`
  - `amenity=clinic`
- We return a normalized list (name + coordinates + type) to the UI and also store it as a snapshot in Neon.  
**Endpoint detail:** The common public endpoint is `https://overpass-api.de/api/interpreter`. 

---

### 5) OpenRouteService (ORS) Directions API — route distance + ETA
**What it’s for:** Estimate **drive distance** and **travel time** for inter-facility transfers (which are a big part of NAS operations).  
**How we’ll use it:**
- FastAPI calls the ORS **v2 directions** endpoint for a driving profile (e.g., `driving-car`) using start/end coordinates.
- We extract the route summary (distance + duration) for:
  - planned destination
  - optionally top 1–3 alternatives (if you want a stronger demo)
- Save that summary into Neon as a snapshot, so you can reload the case later without re-calling ORS every time.  
**Operational constraint:** ORS imposes request limits (including max route distance for driving profiles), so we need graceful fallback if the route is too long or throttled. 

---

### 6) Open‑Meteo Forecast API — current conditions (weather risk)
**What it’s for:** Weather can slow or complicate transport, especially in rainy seasons. We use weather as a simple “risk context” signal.  
**How we’ll use it:**
- FastAPI calls Open‑Meteo’s `/v1/forecast` with:
  - pickup coordinates
  - destination coordinates
  - request “current” variables (temperature, wind, weather code) or the “current_weather” option depending on which output format you standardize on
- Show a compact summary in the UI (e.g., “heavy rain / strong wind” warning)
- Save weather response as a snapshot in Neon for replayable demos. 

---

## How they work together (one “Generate” click)
1. **Astro** sends “Generate” to **FastAPI** (case_id).  
2. **FastAPI** loads the typed case from **Neon**.  
3. FastAPI fetches context:
   - facilities from **Overpass**
   - route/ETA from **OpenRouteService**
   - weather from **Open‑Meteo**
4. FastAPI calls **Ollama chat** with *case + context* and requests strict JSON output.   
5. FastAPI stores results (PCR + flags + snapshots) back into **Neon**.   
6. Astro renders output cards (PCR / QA flags / ops snapshot).

---

## Notes (so the build stays simple)
- If you want **zero geocoding complexity**, require the user to type **lat/lon** (like you planned). Then ORS + Open‑Meteo work reliably with no extra APIs.
- If ORS/Overpass fail (rate limits, downtime), you still generate **PCR + QA flags** from the typed clinical data, and show “Ops context unavailable” instead of failing the whole run.
