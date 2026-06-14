"""Consent endpoints (patient-managed).

Patients grant/revoke consents (e.g. 'ai_processing', 'visit_recording'). Each
submission is a new versioned row, so history is preserved. `has_consent` reads
the latest row per type.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import require_role
from app.database import get_db
from app.models.consent import Consent
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.medication import ConsentCreate, ConsentOut

router = APIRouter(prefix="/me/consents", tags=["consent"])
patient_only = require_role(UserRole.patient)


@router.post("", response_model=ConsentOut, status_code=201)
def grant_consent(payload: ConsentCreate, db: Session = Depends(get_db),
                  patient: User = Depends(patient_only)):
    row = Consent(practice_id=patient.practice_id, patient_id=patient.id,
                  consent_type=payload.consent_type, version=payload.version,
                  granted=payload.granted)
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(db, actor=patient, action_type="consent.update",
                data_accessed=payload.consent_type, detail=f"granted={payload.granted}")
    return row


@router.get("", response_model=list[ConsentOut])
def list_my_consents(db: Session = Depends(get_db), patient: User = Depends(patient_only)):
    return (db.query(Consent)
            .filter(Consent.patient_id == patient.id, Consent.practice_id == patient.practice_id)
            .order_by(Consent.timestamp.desc()).all())
