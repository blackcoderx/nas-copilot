CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
  id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  username   TEXT UNIQUE NOT NULL,
  hashed_pw  TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cases (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  incident_time TIMESTAMPTZ NOT NULL,
  pickup        TEXT NOT NULL,
  destination   TEXT NOT NULL,
  pickup_lat    FLOAT,
  pickup_lon    FLOAT,
  dest_lat      FLOAT,
  dest_lon      FLOAT,
  patient_age   INT,
  patient_sex   TEXT,
  complaint     TEXT NOT NULL,
  vitals        TEXT NOT NULL,
  interventions TEXT,
  notes         TEXT,
  status        TEXT NOT NULL DEFAULT 'DRAFT',
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

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
