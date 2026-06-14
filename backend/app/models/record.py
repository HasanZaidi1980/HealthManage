"""Feature 1 — Medical History Summarization.

- MedicalRecord: a source document. For the prototype, EHR import is simulated
  as a structured JSON upload (per the spec's constraint against using Epic/FHIR
  enterprise APIs). PDF/image uploads can reuse the same row via source_type.
- HealthSummary: the generated One-Page Snapshot. One current row per patient
  (regenerating replaces it). Stores both a patient (plain-language) and a
  clinician snapshot, plus a completeness indicator and timestamp.
- SummaryShare: a tokenized, expiring link to share a snapshot with an outside
  provider from within the app.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_types import GUID, gen_uuid, utcnow


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    practice_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("practices.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)

    source_type: Mapped[str] = mapped_column(String(20), nullable=False, default="json")  # json|pdf|image|fhir
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string of structured clinical data
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class HealthSummary(Base):
    __tablename__ = "health_summaries"
    __table_args__ = (UniqueConstraint("patient_id", name="uq_summary_patient"),)

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    practice_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("practices.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    generated_by: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)

    patient_snapshot: Mapped[str] = mapped_column(Text, nullable=False)    # JSON, plain language
    clinician_snapshot: Mapped[str] = mapped_column(Text, nullable=False)  # JSON, clinical
    completeness: Mapped[str] = mapped_column(Text, nullable=False)        # JSON
    source_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class SummaryShare(Base):
    __tablename__ = "summary_shares"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    practice_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("practices.id"), nullable=False, index=True)
    patient_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    created_by: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    shared_with: Mapped[str] = mapped_column(String(255), nullable=True)  # provider name/email
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
