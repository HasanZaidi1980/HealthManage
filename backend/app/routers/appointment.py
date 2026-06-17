"""Feature 4 — Appointment Tracker.

Doctors create/manage appointments and see their schedule; patients see their
upcoming/past appointments and reminders. Both can view (doctor can generate) an
AI pre-visit checklist. Post-visit, status -> completed with notes archives it.
"""
import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.consent import has_consent
from app.core.deps import require_feature, require_role, scoped_query
from app.database import get_db
from app.models.appointment import Appointment
from app.models.enums import UserRole
from app.models.medication import Medication
from app.models.record import MedicalRecord
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate, AppointmentOut, AppointmentUpdate, ChecklistOut, ReminderOut,
)
from app.services import ai
from app.services.summary import merge_records

router = APIRouter(tags=["appointments"])

doctor_only = require_role(UserRole.doctor)
patient_only = require_role(UserRole.patient)
needs_feature = require_feature("appointments")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _naive(dt: datetime) -> datetime:
    return dt.replace(tzinfo=None) if dt and dt.tzinfo else dt


def _provider_name(db: Session, doctor_id) -> str | None:
    if not doctor_id:
        return None
    d = db.query(User).filter(User.id == doctor_id).first()
    return d.full_name if d else None


def _serialize(db: Session, appt: Appointment) -> AppointmentOut:
    out = AppointmentOut.model_validate(appt)
    out.provider_name = _provider_name(db, appt.doctor_id)
    out.has_checklist = bool(appt.pre_visit_checklist)
    return out


def _get_patient(db, actor, patient_id) -> User:
    p = (scoped_query(db, User, actor)
         .filter(User.id == patient_id, User.role == UserRole.patient).first())
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found in your practice")
    return p


def _get_appt(db, actor, appt_id) -> Appointment:
    a = scoped_query(db, Appointment, actor).filter(Appointment.id == appt_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Appointment not found in your practice")
    return a


def _checklist_inputs(db, actor, patient_id, purpose):
    meds = (scoped_query(db, Medication, actor)
            .filter(Medication.patient_id == patient_id, Medication.is_active.is_(True)).all())
    records = (scoped_query(db, MedicalRecord, actor)
               .filter(MedicalRecord.patient_id == patient_id).all())
    merged = merge_records([json.loads(r.data) for r in records])
    conditions = [c.get("name") for c in merged.get("conditions", []) if c.get("name")]
    return [m.name_generic for m in meds], conditions


# ---------- Doctor ----------
@router.post("/appointments", response_model=AppointmentOut, status_code=201)
def create_appt(payload: AppointmentCreate, db: Session = Depends(get_db),
                doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    _get_patient(db, doctor, payload.patient_id)
    appt = Appointment(
        practice_id=doctor.practice_id, patient_id=payload.patient_id,
        doctor_id=payload.doctor_id or doctor.id,
        scheduled_at=_naive(payload.scheduled_at), location=payload.location,
        telehealth_link=payload.telehealth_link, purpose=payload.purpose)
    db.add(appt)
    db.commit()
    db.refresh(appt)
    write_audit(db, actor=doctor, action_type="appointment.create", data_accessed=f"patient:{payload.patient_id}")
    return _serialize(db, appt)


@router.get("/appointments", response_model=list[AppointmentOut])
def doctor_schedule(range: str = "week", db: Session = Depends(get_db),
                    doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    """Doctor's own schedule. range = day | week | all."""
    appts = (scoped_query(db, Appointment, doctor)
             .filter(Appointment.doctor_id == doctor.id)
             .order_by(Appointment.scheduled_at).all())
    now = _now()
    if range == "day":
        end = now + timedelta(days=1)
        appts = [a for a in appts if now.date() <= a.scheduled_at.date() < end.date() or a.scheduled_at.date() == now.date()]
        appts = [a for a in appts if a.scheduled_at.date() == now.date()]
    elif range == "week":
        end = now + timedelta(days=7)
        appts = [a for a in appts if now - timedelta(days=1) <= a.scheduled_at <= end]
    return [_serialize(db, a) for a in appts]


@router.get("/patients/{patient_id}/appointments", response_model=list[AppointmentOut])
def patient_appts_doctor(patient_id: str, db: Session = Depends(get_db),
                         doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    _get_patient(db, doctor, patient_id)
    appts = (scoped_query(db, Appointment, doctor)
             .filter(Appointment.patient_id == patient_id)
             .order_by(Appointment.scheduled_at.desc()).all())
    return [_serialize(db, a) for a in appts]


@router.patch("/appointments/{appt_id}", response_model=AppointmentOut)
def update_appt(appt_id: str, payload: AppointmentUpdate, db: Session = Depends(get_db),
                doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    appt = _get_appt(db, doctor, appt_id)
    data = payload.model_dump(exclude_unset=True)
    if "scheduled_at" in data and data["scheduled_at"]:
        data["scheduled_at"] = _naive(data["scheduled_at"])
    for k, v in data.items():
        setattr(appt, k, v)
    db.commit()
    db.refresh(appt)
    write_audit(db, actor=doctor, action_type="appointment.update", data_accessed=str(appt_id))
    return _serialize(db, appt)


@router.post("/appointments/{appt_id}/checklist", response_model=ChecklistOut)
def doctor_checklist(appt_id: str, db: Session = Depends(get_db),
                     doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    appt = _get_appt(db, doctor, appt_id)
    meds, conditions = _checklist_inputs(db, doctor, appt.patient_id, appt.purpose)
    checklist = ai.generate_previsit_checklist(purpose=appt.purpose, medications=meds, conditions=conditions)
    appt.pre_visit_checklist = json.dumps(checklist)
    db.commit()
    write_audit(db, actor=doctor, action_type="appointment.checklist", data_accessed=str(appt_id))
    return ChecklistOut(**checklist)


# ---------- Patient ----------
@router.get("/me/appointments", response_model=list[AppointmentOut])
def my_appts(db: Session = Depends(get_db), patient: User = Depends(patient_only), _=Depends(needs_feature)):
    appts = (scoped_query(db, Appointment, patient)
             .filter(Appointment.patient_id == patient.id)
             .order_by(Appointment.scheduled_at).all())
    return [_serialize(db, a) for a in appts]


@router.get("/me/appointments/reminders", response_model=list[ReminderOut])
def my_reminders(db: Session = Depends(get_db), patient: User = Depends(patient_only), _=Depends(needs_feature)):
    now = _now()
    horizon = now + timedelta(days=7)
    appts = (scoped_query(db, Appointment, patient)
             .filter(Appointment.patient_id == patient.id, Appointment.status == "scheduled").all())
    upcoming = sorted([a for a in appts if now <= a.scheduled_at <= horizon],
                      key=lambda a: a.scheduled_at)
    out = []
    for a in upcoming:
        when = a.scheduled_at.strftime("%b %d at %I:%M %p")
        prov = _provider_name(db, a.doctor_id) or "your provider"
        out.append(ReminderOut(appointment_id=a.id, scheduled_at=a.scheduled_at,
                               message=f"Reminder: {a.purpose} with {prov} on {when}."))
    return out


@router.get("/me/appointments/{appt_id}/checklist", response_model=ChecklistOut)
def my_checklist_view(appt_id: str, db: Session = Depends(get_db),
                      patient: User = Depends(patient_only), _=Depends(needs_feature)):
    appt = _get_appt(db, patient, appt_id)
    if not appt.pre_visit_checklist:
        raise HTTPException(status_code=404, detail="No checklist yet")
    return ChecklistOut(**json.loads(appt.pre_visit_checklist))


@router.post("/me/appointments/{appt_id}/checklist", response_model=ChecklistOut)
def my_checklist_generate(appt_id: str, db: Session = Depends(get_db),
                          patient: User = Depends(patient_only), _=Depends(needs_feature)):
    if not has_consent(db, patient_id=patient.id, practice_id=patient.practice_id,
                       consent_type="ai_processing"):
        raise HTTPException(status_code=403, detail="AI processing consent required.")
    appt = _get_appt(db, patient, appt_id)
    meds, conditions = _checklist_inputs(db, patient, patient.id, appt.purpose)
    checklist = ai.generate_previsit_checklist(purpose=appt.purpose, medications=meds, conditions=conditions)
    appt.pre_visit_checklist = json.dumps(checklist)
    db.commit()
    write_audit(db, actor=patient, action_type="appointment.checklist", data_accessed=str(appt_id))
    return ChecklistOut(**checklist)
