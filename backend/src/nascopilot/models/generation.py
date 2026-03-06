from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from nascopilot.models.flag import QualityFlag


class GenerationOut(BaseModel):
    id: UUID
    case_id: UUID
    pcr_text: str
    recommendation: str | None
    model_name: str | None
    facilities_json: Any | None
    route_json: Any | None
    weather_json: Any | None
    created_at: datetime
    flags: list[QualityFlag] = []
