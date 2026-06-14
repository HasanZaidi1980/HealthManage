"""Feature 2 — Active Medication List.

A medication belongs to a patient within a practice. It stores both a
clinician-facing `clinical_indication` and a patient-facing
`plain_language_purpose` (AI-generated). Role-appropriate views are produced by
the schemas, not by storing duplicate rows.
"""
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_types import GUID, gen_uuid, utcnow


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    practice_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("practices.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    prescribed_by: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)

    name_generic: Mapped[str] = mapped_column(String(160), nullable=False)
    name_brand: Mapped[str] = mapped_column(String(160), nullable=True)
    dosage: Mapped[str] = mapped_column(String(120), nullable=False)        # e.g. "500 mg"
    frequency: Mapped[str] = mapped_column(String(120), nullable=False)     # e.g. "twice daily"
    prescribing_provider: Mapped[str] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    refill_due_date: Mapped[date] = mapped_column(Date, nullable=True)

    # Doctor view
    clinical_indication: Mapped[str] = mapped_column(Text, nullable=True)
    # Patient view (AI-generated, plain language)
    plain_language_purpose: Mapped[str] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
