"""Consent helpers. Required before PHI is sent to AI on the patient's behalf."""
from sqlalchemy.orm import Session
from app.models.consent import Consent


def has_consent(db: Session, *, patient_id, practice_id, consent_type: str) -> bool:
    """True if the patient's most recent record for this type is `granted`."""
    latest = (db.query(Consent)
              .filter(Consent.patient_id == patient_id,
                      Consent.practice_id == practice_id,
                      Consent.consent_type == consent_type)
              .order_by(Consent.timestamp.desc())
              .first())
    return bool(latest and latest.granted)
