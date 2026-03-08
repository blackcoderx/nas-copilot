from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class VitalsSet(BaseModel):
    bp_sys:  int   | None = None
    bp_dia:  int   | None = None
    hr:      int   | None = None
    rr:      int   | None = None
    spo2:    int   | None = None
    gcs:     int   | None = None
    pain:    int   | None = None  # 0-10
    temp_c:  float | None = None
    time:    datetime | None = None


class CaseCreate(BaseModel):
    # Time chain
    dispatch_time:      datetime | None = None
    incident_time:      datetime
    on_scene_time:      datetime | None = None
    transport_start:    datetime | None = None
    arrival_time:       datetime | None = None
    transfer_care_time: datetime | None = None

    # Locations
    pickup:      str
    destination: str
    pickup_lat:  float | None = None
    pickup_lon:  float | None = None
    dest_lat:    float | None = None
    dest_lon:    float | None = None

    # Transport
    transport_mode: str = "non-emergent"

    # IFT context
    sending_physician:  str | None = None
    sending_diagnosis:  str | None = None
    referral_reason:    str | None = None
    receiving_provider: str | None = None

    # Patient demographics
    patient_name: str | None = None
    patient_age:  int | None = None
    patient_sex:  str | None = None

    # SAMPLE history
    complaint:           str
    allergies:           str | None = None
    current_medications: str | None = None
    past_medical_hx:     str | None = None
    last_oral_intake:    str | None = None
    events_leading:      str | None = None

    # Clinical
    vitals_set_1:  VitalsSet | None = None
    vitals_set_2:  VitalsSet | None = None
    interventions: str | None = None
    notes:         str | None = None

    # Crew
    crew_names: str | None = None


class CaseOut(BaseModel):
    id:                  UUID
    dispatch_time:       datetime | None
    incident_time:       datetime
    on_scene_time:       datetime | None
    transport_start:     datetime | None
    arrival_time:        datetime | None
    transfer_care_time:  datetime | None
    pickup:              str
    destination:         str
    pickup_lat:          float | None
    pickup_lon:          float | None
    dest_lat:            float | None
    dest_lon:            float | None
    transport_mode:      str
    sending_physician:   str | None
    sending_diagnosis:   str | None
    referral_reason:     str | None
    receiving_provider:  str | None
    patient_name:        str | None
    patient_age:         int | None
    patient_sex:         str | None
    complaint:           str
    allergies:           str | None
    current_medications: str | None
    past_medical_hx:     str | None
    last_oral_intake:    str | None
    events_leading:      str | None
    vitals_set_1:        dict | None
    vitals_set_2:        dict | None
    interventions:       str | None
    notes:               str | None
    crew_names:          str | None
    status:              str
    created_at:          datetime
    updated_at:          datetime


class CaseListItem(BaseModel):
    id:           UUID
    complaint:    str
    pickup:       str
    destination:  str
    patient_name: str | None
    status:       str
    created_at:   datetime
