"""Importing every model here ensures Base.metadata sees all tables."""
from app.models.audit import AuditLog
from app.models.consent import Consent
from app.models.enums import SubscriptionTier, UserRole
from app.models.explanation import ConditionExplanation
from app.models.medication import Medication
from app.models.practice import Practice
from app.models.record import HealthSummary, MedicalRecord, SummaryShare
from app.models.user import User

__all__ = ["Practice", "User", "AuditLog", "Consent", "Medication",
           "MedicalRecord", "HealthSummary", "SummaryShare", "ConditionExplanation",
           "UserRole", "SubscriptionTier"]
