# NAS Copilot GH

An AI-assisted EMS documentation platform built for Ghana's National Ambulance Service. EMTs enter a patient case once and instantly receive a formatted Patient Care Report (PCR), quality flags, a clinical recommendation, and an operational context snapshot — all saved for audit and analytics.

---

## The Problem

Ghana NAS EMTs document on paper under pressure. The result: incomplete records, inconsistent formats, no aggregated system data, and leadership with no evidence to justify budget requests or fleet replacement. NAS Copilot digitizes the documentation workflow end-to-end and surfaces the data for decision-making at every level.

---

## Features

### Core Workflow (EMT)
- **Structured case entry** — full SAMPLE history, two vitals sets, time chain (dispatch → incident → on-scene → transport → arrival → transfer of care), GPS coordinates, IFT context (sending physician, referral reason, receiving provider)
- **AI PCR generation** — one click produces a clean, formatted narrative PCR from the typed inputs
- **Quality flags** — deterministic rule checks + AI-generated flags, sorted by severity (high → medium → low), each with a specific corrective action
- **AI triage severity score** — color-coded risk level (red/orange/yellow/green) with clinical reasoning and time-critical flags
- **Operational context** — route distance & ETA (OpenRouteService), weather at pickup & destination (Open-Meteo), and up to 5 nearby facilities (Overpass/OSM), all fetched concurrently and saved as replayable snapshots
- **Finalize & export** — cases can be locked as FINAL and exported as JSON

### Outcome Feedback Loop
- Each case gets a unique public outcome token link
- Hospital staff submit patient status (admitted / discharged / deceased / transferred), admission ward, and confirmed diagnosis — no login required
- EMTs see the outcome on their case detail page, closing the loop between pre-hospital care and hospital result

### Facility Capacity Board
- Hospital admins publish live ICU bed availability, surgical theater status, blood bank level, and maternity capacity
- Status auto-expires after 4 hours to prevent stale data
- All hospitals' live status is visible on a shared board, helping EMTs select the right destination

### Aggregate Analytics Dashboard (Admin/Superadmin)
- Cases per day over the last 30 days (line chart)
- Triage severity distribution (pie chart)
- Top 5 chief complaints (horizontal bar chart)
- Transport mode split — IFT vs scene response (doughnut chart)
- Outcomes summary (bar chart)
- Top QA flags by frequency (ranked table)
- Incident location heatmap (Leaflet.js with pickup coordinates)
- PCR completion rate KPI
- One-click CSV export for government/donor reporting
- Role-scoped: admins see their hospital's data; superadmin sees all hospitals

### Role-Based Access Control
| Role | Access |
|------|--------|
| **EMT** | Create and view own cases, view outcomes for own cases |
| **Admin** | View all hospital cases, manage staff, update facility status, view hospital analytics |
| **Superadmin** | View all cases globally, register hospitals and admins, view aggregate analytics |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Astro 5, TypeScript, Chart.js, Leaflet.js |
| Backend | Python 3.13, FastAPI (async), Pydantic |
| Database | PostgreSQL via Neon (asyncpg) |
| AI | Ollama Cloud (`kimi-k2.5:cloud`) |
| Maps / Routing | OpenRouteService, Overpass API (OSM) |
| Weather | Open-Meteo |
| Auth | JWT (python-jose), bcrypt |

---

## Project Structure

```
nas-copilot/
├── backend/
│   └── src/nascopilot/
│       ├── main.py              # FastAPI app, lifespan, router registration
│       ├── config.py            # Settings from .env
│       ├── database.py          # asyncpg connection pool
│       ├── dependencies.py      # get_current_user, require_admin, require_superadmin
│       ├── db/
│       │   ├── schema.sql       # Full database schema
│       │   └── queries.py       # All database query functions
│       ├── routers/
│       │   ├── auth.py          # Login, user/hospital registration
│       │   ├── cases.py         # Case CRUD, PCR generation, finalize, export
│       │   ├── outcomes.py      # Public outcome submission + retrieval
│       │   ├── facilities.py    # Facility capacity status
│       │   └── analytics.py     # Aggregate analytics summary
│       ├── models/              # Pydantic schemas (case, outcome, facility, generation, flag)
│       └── services/
│           ├── generate.py      # Generation orchestrator
│           ├── ai.py            # Prompt building + Ollama API call
│           ├── openroute.py     # Route ETA
│           ├── overpass.py      # Nearby facility search
│           └── weather.py       # Weather context
└── frontend/
    └── src/
        ├── layouts/Base.astro   # Global layout, nav, CSS variables
        └── pages/
            ├── login.astro
            ├── dashboard.astro      # EMT case list
            ├── analytics.astro      # Admin/Superadmin analytics dashboard
            ├── cases/
            │   ├── new.astro        # Case creation form
            │   └── [id].astro       # Case detail + generation display
            ├── outcomes/
            │   └── [token].astro    # Public outcome submission (no auth)
            ├── admin/
            │   ├── index.astro      # Admin panel (staff + cases)
            │   ├── facility-status.astro
            │   └── users/new.astro
            └── superadmin/
                └── index.astro
```

---

## API Endpoints

### Auth
| Method | Path | Access | Description |
|--------|------|--------|-------------|
| POST | `/auth/login` | Public | Returns JWT token + role |
| POST | `/auth/register/emt` | Admin | Register EMT for a hospital |
| POST | `/auth/register/admin` | Superadmin | Register hospital admin |
| GET | `/auth/users` | Admin | List hospital staff |
| GET | `/auth/hospitals` | Superadmin | List all hospitals |

### Cases
| Method | Path | Access | Description |
|--------|------|--------|-------------|
| POST | `/cases` | EMT+ | Create case |
| GET | `/cases` | EMT+ | List cases (role-scoped) |
| GET | `/cases/{id}` | EMT+ | Get case with latest generation and flags |
| POST | `/cases/{id}/generate` | EMT+ | Run AI generation |
| PATCH | `/cases/{id}/finalize` | EMT+ | Lock case as FINAL |
| GET | `/cases/{id}/export` | EMT+ | Export as JSON |

### Outcomes
| Method | Path | Access | Description |
|--------|------|--------|-------------|
| GET | `/outcomes/{token}` | Public | Get case summary for outcome form |
| POST | `/outcomes/{token}` | Public | Submit patient outcome |
| GET | `/outcomes/by-case/{id}` | EMT+ | Get outcome for a case |

### Facilities
| Method | Path | Access | Description |
|--------|------|--------|-------------|
| GET | `/facilities/status` | Public | Live capacity for all hospitals |
| PUT | `/facilities/status` | Admin | Update own hospital's capacity |

### Analytics
| Method | Path | Access | Description |
|--------|------|--------|-------------|
| GET | `/analytics/summary` | Admin+ | Aggregated dashboard data |

---

## Database Schema

```
users          — id, username, hashed_pw, role, hospital_id, full_name
hospitals      — id, name
cases          — id, created_by, status (DRAFT|FINAL), outcome_token,
                 time chain (6 timestamps), locations (text + lat/lon),
                 transport_mode, IFT context (4 fields),
                 patient (name, age, sex), SAMPLE history (6 fields),
                 vitals_set_1/2 (JSONB), interventions, notes, crew_names
generations    — id, case_id, pcr_text, recommendation, model_name,
                 facilities_json, route_json, weather_json, triage_json
quality_flags  — id, generation_id, severity, issue, action
outcomes       — id, case_id, patient_status, admission_ward,
                 confirmed_diagnosis, notes, submitted_at
facility_status — id, hospital_id, icu_beds_available, surgical_theater,
                  blood_bank, maternity, special_alert, updated_at, expires_at
```

---

## Setup

### Prerequisites
- Python 3.13+
- Node.js 18+
- A [Neon](https://neon.tech) PostgreSQL database
- An Ollama Cloud API key

### Backend

```bash
cd backend
pip install -e .

# Create .env
cp .env.example .env
# Fill in: DATABASE_URL, OLLAMA_API_KEY, JWT_SECRET,
#          ORS_API_KEY, SUPERADMIN_USERNAME, SUPERADMIN_PASSWORD

# Apply schema
psql $DATABASE_URL < src/nascopilot/db/schema.sql

# Start
uvicorn nascopilot.main:app --reload
```

### Frontend

```bash
cd frontend
npm install

# Create .env
echo "PUBLIC_API_URL=http://localhost:8000" > .env

# Start
npm run dev
```

---

## Environment Variables

### Backend (`.env`)
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Neon PostgreSQL connection string (include `sslmode=require`) |
| `JWT_SECRET` | Random secret for signing JWT tokens |
| `OLLAMA_API_KEY` | Ollama Cloud API key |
| `OLLAMA_BASE_URL` | Ollama API base URL (default: `https://ollama.com`) |
| `OLLAMA_MODEL` | Model name (default: `kimi-k2.5:cloud`) |
| `ORS_API_KEY` | OpenRouteService API key |
| `CORS_ORIGINS` | Comma-separated allowed origins (e.g. `http://localhost:4321`) |
| `SUPERADMIN_USERNAME` | Auto-created superadmin username on first boot |
| `SUPERADMIN_PASSWORD` | Auto-created superadmin password on first boot |

### Frontend (`.env`)
| Variable | Description |
|----------|-------------|
| `PUBLIC_API_URL` | Backend base URL |

---

## How the Generate Flow Works

1. EMT clicks **Generate PCR** on a case
2. Frontend calls `POST /cases/{id}/generate`
3. Backend loads the case from PostgreSQL
4. Three external API calls run concurrently:
   - **Overpass** — finds up to 5 hospitals/clinics within 20 km of pickup
   - **OpenRouteService** — driving distance and ETA to destination
   - **Open-Meteo** — current weather at pickup and destination
5. Backend builds a structured prompt with case data + all context
6. **Ollama** returns JSON: `pcr_text`, `recommendation`, `triage` (color + reasoning), `flags`
7. Backend merges AI flags with deterministic rule-based flags and deduplicates
8. Everything is saved to PostgreSQL (generation + flags as separate rows)
9. Frontend renders: PCR narrative, quality flags sorted by severity, triage badge, ops snapshot

---

## Design Decisions

- **No geocoding** — users enter lat/lon directly; keeps the stack simple and works reliably without a paid geocoding API
- **Graceful degradation** — if ORS/Overpass/Open-Meteo fail, PCR + flags still generate; ops context shows "unavailable"
- **Replayable snapshots** — route/weather/facilities are stored as JSONB alongside each generation, so reloading a case never re-calls external APIs
- **Deterministic + AI flags** — rule-based checks (missing allergies, pain score, etc.) run every time regardless of AI output, ensuring baseline quality coverage
- **Public outcome tokens** — hospital staff don't need accounts; a unique URL per case is enough for outcome submission
- **4-hour facility status TTL** — prevents stale capacity data from misleading EMTs without requiring constant manual updates
