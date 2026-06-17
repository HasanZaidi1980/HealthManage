"""Feature 3 — AI Condition Explainer.

Conditions are derived from the patient's uploaded medical records. Patients (and
doctors, for patient-ready output) can request an explanation at three levels:
simple / moderate / detailed. Every explanation carries the required disclaimer.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.consent import has_consent
from app.core.deps import require_feature, require_role, scoped_query
from app.database import get_db
from app.models.enums import UserRole
from app.models.record import MedicalRecord
from app.models.user import User
from app.schemas.condition import ConditionOut, ExplainRequest, ExplanationOut
from app.services import ai
from app.services.ai import EXPLAINER_DISCLAIMER
from app.services.summary import merge_records

router = APIRouter(tags=["conditions"])

doctor_only = require_role(UserRole.doctor)
patient_only = require_role(UserRole.patient)
needs_feature = require_feature("explainer")


def _get_patient(db, actor, patient_id) -> User:
    p = (scoped_query(db, User, actor)
         .filter(User.id == patient_id, User.role == UserRole.patient).first())
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found in your practice")
    return p


def _conditions_for(db, actor, patient_id) -> list[ConditionOut]:
    records = (scoped_query(db, MedicalRecord, actor)
               .filter(MedicalRecord.patient_id == patient_id).all())
    merged = merge_records([json.loads(r.data) for r in records])
    out, seen = [], set()
    for c in merged.get("conditions", []):
        name = c.get("name")
        if name and name.lower() not in seen:
            seen.add(name.lower())
            out.append(ConditionOut(name=name, status=c.get("status")))
    return out


def _explain(condition: str, level: str) -> ExplanationOut:
    text = ai.explain_condition(condition=condition, level=level)
    return ExplanationOut(condition=condition, level=level, explanation=text,
                          disclaimer=EXPLAINER_DISCLAIMER)


# ---------- Patient ----------
@router.get("/me/conditions", response_model=list[ConditionOut])
def my_conditions(db: Session = Depends(get_db), patient: User = Depends(patient_only),
                  _=Depends(needs_feature)):
    return _conditions_for(db, patient, patient.id)


@router.post("/me/conditions/explain", response_model=ExplanationOut)
def my_explain(payload: ExplainRequest, db: Session = Depends(get_db),
               patient: User = Depends(patient_only), _=Depends(needs_feature)):
    if not has_consent(db, patient_id=patient.id, practice_id=patient.practice_id,
                       consent_type="ai_processing"):
        raise HTTPException(status_code=403, detail="AI processing consent required.")
    write_audit(db, actor=patient, action_type="condition.explain", data_accessed=payload.condition)
    return _explain(payload.condition, payload.level)


# ---------- Doctor ----------
@router.get("/patients/{patient_id}/conditions", response_model=list[ConditionOut])
def patient_conditions(patient_id: str, db: Session = Depends(get_db),
                       doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    _get_patient(db, doctor, patient_id)
    return _conditions_for(db, doctor, patient_id)


@router.post("/patients/{patient_id}/conditions/explain", response_model=ExplanationOut)
def doctor_explain(patient_id: str, payload: ExplainRequest, db: Session = Depends(get_db),
                   doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    _get_patient(db, doctor, patient_id)
    write_audit(db, actor=doctor, action_type="condition.explain",
                data_accessed=f"patient:{patient_id}:{payload.condition}")
    return _explain(payload.condition, payload.level)
