"""Persistent cache for Feature 3 explanations.

Explanations depend only on (condition, level) — not on the patient — so they are
cached once per practice and reused, instead of re-calling the AI on every click.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_types import GUID, gen_uuid, utcnow


class ConditionExplanation(Base):
    __tablename__ = "condition_explanations"
    __table_args__ = (UniqueConstraint("practice_id", "condition", "level", name="uq_cond_expl"),)

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    practice_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("practices.id", ondelete="CASCADE"), nullable=False, index=True)
    condition: Mapped[str] = mapped_column(String(200), nullable=False)  # normalized lowercase
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
