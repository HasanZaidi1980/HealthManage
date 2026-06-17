"""Feature 4 — Appointment schemas."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    scheduled_at: datetime
    purpose: str = Field(min_length=1, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    telehealth_link: str | None = Field(default=None, max_length=500)
    doctor_id: uuid.UUID | None = None  # defaults to the creating doctor


class AppointmentUpdate(BaseModel):
    status: str | None = Field(default=None, pattern="^(scheduled|completed|cancelled)$")
    notes: str | None = None
    scheduled_at: datetime | None = None
    purpose: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)
    telehealth_link: str | None = Field(default=None, max_length=500)


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None
    provider_name: str | None = None
    scheduled_at: datetime
    location: str | None
    telehealth_link: str | None
    purpose: str
    status: str
    notes: str | None
    has_checklist: bool = False


class ChecklistOut(BaseModel):
    questions: list[str] = []
    documents: list[str] = []
    medications_to_mention: list[str] = []


class ReminderOut(BaseModel):
    appointment_id: uuid.UUID
    scheduled_at: datetime
    message: str
