"""Feature 4 — Appointment Tracker model."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_types import GUID, gen_uuid, utcnow


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    practice_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("practices.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    telehealth_link: Mapped[str] = mapped_column(String(500), nullable=True)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")  # scheduled|completed|cancelled

    notes: Mapped[str] = mapped_column(Text, nullable=True)              # post-visit
    pre_visit_checklist: Mapped[str] = mapped_column(Text, nullable=True)  # JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
