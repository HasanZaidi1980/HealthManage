"""Feature 1 schemas — records, snapshot, sharing."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecordCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source_type: str = Field(default="json", pattern="^(json|pdf|image|fhir)$")
    # Structured clinical data: {conditions:[...], allergies:[...], labs:[...], imaging:[...]}
    data: dict


class RecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    source_type: str
    created_at: datetime


class Snapshot(BaseModel):
    chief_conditions: list[str] = []
    current_medications: list[str] = []
    known_allergies: list[str] = []
    recent_labs_imaging: list[str] = []
    recommended_followups: list[str] = []
    disclaimer: str


class HealthSummaryOut(BaseModel):
    patient_id: uuid.UUID
    snapshot: Snapshot
    completeness: dict
    source_record_count: int
    last_updated: datetime


class ShareCreate(BaseModel):
    shared_with: str | None = Field(default=None, max_length=255)
    expires_in_days: int = Field(default=7, ge=1, le=90)


class ShareOut(BaseModel):
    token: str
    share_url: str
    shared_with: str | None
    expires_at: datetime
