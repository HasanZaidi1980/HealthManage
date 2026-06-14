from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.db_types import GUID, gen_uuid, utcnow


class Consent(Base):
    __tablename__ = "consents"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    practice_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("practices.id"), nullable=False, index=True)
    patient_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=False, index=True)
    consent_type: Mapped[str] = mapped_column(String(60), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
