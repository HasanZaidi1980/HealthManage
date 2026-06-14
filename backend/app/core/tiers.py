"""Subscription tier -> feature flags and seat limits. Enforced server-side."""
from app.models.enums import SubscriptionTier

STARTER_FEATURES = {"summary", "medications", "explainer", "appointments"}
PRO_FEATURES = STARTER_FEATURES | {"visit_recording", "education"}
ENTERPRISE_FEATURES = PRO_FEATURES | {"custom_branding", "ehr_integration"}

TIER_FEATURES: dict[SubscriptionTier, set[str]] = {
    SubscriptionTier.starter: STARTER_FEATURES,
    SubscriptionTier.professional: PRO_FEATURES,
    SubscriptionTier.enterprise: ENTERPRISE_FEATURES,
}

TIER_LIMITS: dict[SubscriptionTier, dict[str, int | None]] = {
    SubscriptionTier.starter: {"max_doctors": 3, "max_patients": 200},
    SubscriptionTier.professional: {"max_doctors": 10, "max_patients": None},
    SubscriptionTier.enterprise: {"max_doctors": None, "max_patients": None},
}


def tier_has_feature(tier: SubscriptionTier, feature: str) -> bool:
    return feature in TIER_FEATURES.get(tier, set())


def tier_limit(tier: SubscriptionTier, key: str) -> int | None:
    return TIER_LIMITS.get(tier, {}).get(key)
