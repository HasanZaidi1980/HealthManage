from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.db_types import GUID, gen_uuid, utcnow
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    practice_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("practices.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    practice: Mapped["Practice"] = relationship(back_populates="users")  # noqa: F821
