"""Auth, user, and practice schemas."""
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.enums import SubscriptionTier, UserRole


class RegisterPracticeRequest(BaseModel):
    practice_name: str = Field(min_length=2, max_length=255)
    subscription_tier: SubscriptionTier = SubscriptionTier.starter
    admin_email: EmailStr
    admin_password: str = Field(min_length=8, max_length=128)
    admin_full_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    practice_id: uuid.UUID


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    practice_id: uuid.UUID
    created_at: datetime


class PracticeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    subscription_tier: SubscriptionTier
    is_active: bool
    created_at: datetime


class PracticeBilling(BaseModel):
    practice: PracticeOut
    features: list[str]
    doctor_count: int
    patient_count: int
    max_doctors: int | None
    max_patients: int | None
