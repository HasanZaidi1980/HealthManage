from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.db_types import GUID, gen_uuid, utcnow
from app.models.enums import SubscriptionTier


class Practice(Base):
    __tablename__ = "practices"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier, name="subscription_tier"), nullable=False, default=SubscriptionTier.starter)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    users: Mapped[list["User"]] = relationship(back_populates="practice")  # noqa: F821
