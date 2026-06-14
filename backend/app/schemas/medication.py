"""Medication and consent schemas.

Two medication output shapes enforce the role split:
  - MedicationDoctorOut  exposes clinical_indication (clinician view)
  - MedicationPatientOut omits it, exposing only plain_language_purpose
"""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------- Medications ----------
class MedicationCreate(BaseModel):
    patient_id: uuid.UUID
    name_generic: str = Field(min_length=1, max_length=160)
    name_brand: str | None = Field(default=None, max_length=160)
    dosage: str = Field(min_length=1, max_length=120)
    frequency: str = Field(min_length=1, max_length=120)
    prescribing_provider: str | None = Field(default=None, max_length=200)
    start_date: date | None = None
    refill_due_date: date | None = None
    clinical_indication: str | None = None  # optional; AI fills if omitted


class _MedicationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name_generic: str
    name_brand: str | None
    dosage: str
    frequency: str
    prescribing_provider: str | None
    start_date: date | None
    refill_due_date: date | None
    is_active: bool


class MedicationPatientOut(_MedicationBase):
    """No clinical_indication — patients only see plain language."""
    plain_language_purpose: str | None


class MedicationDoctorOut(_MedicationBase):
    patient_id: uuid.UUID
    prescribed_by: uuid.UUID | None
    clinical_indication: str | None
    plain_language_purpose: str | None
    created_at: datetime


class InteractionFlag(BaseModel):
    drug_a: str
    drug_b: str
    severity: str
    note: str


# ---------- Consent ----------
class ConsentCreate(BaseModel):
    consent_type: str = Field(min_length=2, max_length=60)
    version: str = Field(min_length=1, max_length=20)
    granted: bool = True


class ConsentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    consent_type: str
    version: str
    granted: bool
    timestamp: datetime
