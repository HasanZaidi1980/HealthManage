import enum


class UserRole(str, enum.Enum):
    patient = "patient"
    doctor = "doctor"
    admin = "admin"


class SubscriptionTier(str, enum.Enum):
    starter = "starter"
    professional = "professional"
    enterprise = "enterprise"
