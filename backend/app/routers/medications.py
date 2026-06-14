"""Feature 2 — Active Medication List endpoints.

Role split:
  - Doctors create medications and read any patient's full clinical view.
  - Patients read only their own list, in plain language (no clinical_indication).
  - Admins have no access here (PHI).

Every endpoint is gated by the 'medications' feature flag (all tiers include it)
and writes an audit row, since medication data is PHI.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.consent import has_consent
from app.core.deps import get_current_user, require_feature, require_role, scoped_query
from app.database import get_db
from app.models.enums import UserRole
from app.models.medication import Medication
from app.models.user import User
from app.schemas.medication import (
    InteractionFlag,
    MedicationCreate,
    MedicationDoctorOut,
    MedicationPatientOut,
)
from app.services import ai

router = APIRouter(tags=["medications"])

doctor_only = require_role(UserRole.doctor)
patient_only = require_role(UserRole.patient)
needs_feature = require_feature("medications")


def _get_patient_in_practice(db: Session, actor: User, patient_id) -> User:
    patient = (scoped_query(db, User, actor)
               .filter(User.id == patient_id, User.role == UserRole.patient).first())
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found in your practice")
    return patient


def _patient_meds(db: Session, actor: User, patient_id):
    return (scoped_query(db, Medication, actor)
            .filter(Medication.patient_id == patient_id)
            .order_by(Medication.created_at).all())


# ---------- Doctor: create ----------
@router.post("/medications", response_model=MedicationDoctorOut, status_code=201)
def create_medication(payload: MedicationCreate, db: Session = Depends(get_db),
                      doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    _get_patient_in_practice(db, doctor, payload.patient_id)

    # AI fills the role-specific text fields (de-identified inputs only).
    plain = ai.generate_medication_purpose(
        generic=payload.name_generic, brand=payload.name_brand,
        dosage=payload.dosage, frequency=payload.frequency, audience="patient")
    clinical = payload.clinical_indication or ai.generate_medication_purpose(
        generic=payload.name_generic, brand=payload.name_brand,
        dosage=payload.dosage, frequency=payload.frequency, audience="doctor")

    med = Medication(
        practice_id=doctor.practice_id, patient_id=payload.patient_id, prescribed_by=doctor.id,
        name_generic=payload.name_generic, name_brand=payload.name_brand,
        dosage=payload.dosage, frequency=payload.frequency,
        prescribing_provider=payload.prescribing_provider or doctor.full_name,
        start_date=payload.start_date, refill_due_date=payload.refill_due_date,
        clinical_indication=clinical, plain_language_purpose=plain)
    db.add(med)
    db.commit()
    db.refresh(med)
    write_audit(db, actor=doctor, action_type="medication.create",
                data_accessed=f"patient:{payload.patient_id}")
    return med


# ---------- Doctor: read a patient's full list ----------
@router.get("/patients/{patient_id}/medications", response_model=list[MedicationDoctorOut])
def doctor_list(patient_id: str, db: Session = Depends(get_db),
                doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    _get_patient_in_practice(db, doctor, patient_id)
    write_audit(db, actor=doctor, action_type="medication.read", data_accessed=f"patient:{patient_id}")
    return _patient_meds(db, doctor, patient_id)


@router.get("/patients/{patient_id}/medications/interactions", response_model=list[InteractionFlag])
def doctor_interactions(patient_id: str, db: Session = Depends(get_db),
                        doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    _get_patient_in_practice(db, doctor, patient_id)
    meds = _patient_meds(db, doctor, patient_id)
    write_audit(db, actor=doctor, action_type="medication.interaction_check",
                data_accessed=f"patient:{patient_id}")
    return ai.check_interactions([m.name_generic for m in meds if m.is_active])


# ---------- Patient: read own list (plain-language view) ----------
@router.get("/me/medications", response_model=list[MedicationPatientOut])
def my_meds(db: Session = Depends(get_db), patient: User = Depends(patient_only), _=Depends(needs_feature)):
    write_audit(db, actor=patient, action_type="medication.read", data_accessed="self")
    return _patient_meds(db, patient, patient.id)


@router.get("/me/medications/interactions", response_model=list[InteractionFlag])
def my_interactions(db: Session = Depends(get_db), patient: User = Depends(patient_only),
                    _=Depends(needs_feature)):
    # Patient-initiated AI use requires consent on record.
    if not has_consent(db, patient_id=patient.id, practice_id=patient.practice_id,
                       consent_type="ai_processing"):
        raise HTTPException(status_code=403,
                            detail="AI processing consent required. Grant it under Consent Management.")
    meds = _patient_meds(db, patient, patient.id)
    write_audit(db, actor=patient, action_type="medication.interaction_check", data_accessed="self")
    return ai.check_interactions([m.name_generic for m in meds if m.is_active])


# ---------- Doctor: deactivate ----------
@router.patch("/medications/{med_id}/deactivate", response_model=MedicationDoctorOut)
def deactivate(med_id: str, db: Session = Depends(get_db),
               doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    med = scoped_query(db, Medication, doctor).filter(Medication.id == med_id).first()
    if not med:
        raise HTTPException(status_code=404, detail="Medication not found in your practice")
    med.is_active = False
    db.commit()
    db.refresh(med)
    write_audit(db, actor=doctor, action_type="medication.deactivate", data_accessed=str(med_id))
    return med
