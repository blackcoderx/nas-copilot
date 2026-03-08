CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username   TEXT UNIQUE NOT NULL,
  hashed_pw  TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cases (
  id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  -- Time chain
  dispatch_time       TIMESTAMPTZ,
  incident_time       TIMESTAMPTZ NOT NULL,
  on_scene_time       TIMESTAMPTZ,
  transport_start     TIMESTAMPTZ,
  arrival_time        TIMESTAMPTZ,
  transfer_care_time  TIMESTAMPTZ,

  -- Locations
  pickup              TEXT NOT NULL,
  destination         TEXT NOT NULL,
  pickup_lat          FLOAT,
  pickup_lon          FLOAT,
  dest_lat            FLOAT,
  dest_lon            FLOAT,

  -- Transport
  transport_mode      TEXT NOT NULL DEFAULT 'non-emergent',

  -- IFT context
  sending_physician   TEXT,
  sending_diagnosis   TEXT,
  referral_reason     TEXT,
  receiving_provider  TEXT,

  -- Patient demographics
  patient_name        TEXT,
  patient_age         INT,
  patient_sex         TEXT,

  -- SAMPLE history
  complaint           TEXT NOT NULL,
  allergies           TEXT,
  current_medications TEXT,
  past_medical_hx     TEXT,
  last_oral_intake    TEXT,
  events_leading      TEXT,

  -- Clinical
  vitals              TEXT,
  vitals_set_1        JSONB,
  vitals_set_2        JSONB,
  interventions       TEXT,
  notes               TEXT,

  -- Crew
  crew_names          TEXT,

  status              TEXT NOT NULL DEFAULT 'DRAFT',
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Idempotent migrations: add new columns to existing tables
ALTER TABLE cases ADD COLUMN IF NOT EXISTS dispatch_time       TIMESTAMPTZ;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS on_scene_time       TIMESTAMPTZ;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS transport_start     TIMESTAMPTZ;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS arrival_time        TIMESTAMPTZ;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS transfer_care_time  TIMESTAMPTZ;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS transport_mode      TEXT NOT NULL DEFAULT 'non-emergent';
ALTER TABLE cases ADD COLUMN IF NOT EXISTS sending_physician   TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS sending_diagnosis   TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS referral_reason     TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS receiving_provider  TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS patient_name        TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS allergies           TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS current_medications TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS past_medical_hx     TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS last_oral_intake    TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS events_leading      TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS vitals_set_1        JSONB;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS vitals_set_2        JSONB;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS crew_names          TEXT;
ALTER TABLE cases ALTER COLUMN vitals DROP NOT NULL;

CREATE TABLE IF NOT EXISTS generations (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  case_id         UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  pcr_text        TEXT NOT NULL,
  recommendation  TEXT,
  model_name      TEXT,
  facilities_json JSONB,
  route_json      JSONB,
  weather_json    JSONB,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quality_flags (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  generation_id UUID NOT NULL REFERENCES generations(id) ON DELETE CASCADE,
  severity      TEXT NOT NULL,
  issue         TEXT NOT NULL,
  action        TEXT NOT NULL
);
