from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.db_types import GUID, gen_uuid, utcnow


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    practice_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("practices.id"), nullable=True, index=True)
    user_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("users.id"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    data_accessed: Mapped[str] = mapped_column(String(255), nullable=True)
    detail: Mapped[str] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False, index=True)
