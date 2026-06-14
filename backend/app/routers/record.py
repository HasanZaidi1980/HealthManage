"""Feature 1 — Medical History Summarization (One-Page Snapshot).

Patients/doctors upload structured source records; the AI assembles a One-Page
Snapshot with role-appropriate phrasing (patient = plain language, doctor =
clinical). Snapshots are downloadable as PDF and shareable via expiring token.

Generating a summary sends de-identified clinical data to the AI, so it requires
the patient's `ai_processing` consent on file.
"""
import json
import secrets
from datetime import timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.consent import has_consent
from app.core.deps import require_feature, require_role, scoped_query
from app.database import get_db
from app.db_types import utcnow
from app.models.enums import UserRole
from app.models.medication import Medication
from app.models.record import HealthSummary, MedicalRecord, SummaryShare
from app.models.user import User
from app.schemas.record import (
    HealthSummaryOut, RecordCreate, RecordOut, ShareCreate, ShareOut,
)
from app.services import ai, pdf
from app.services.summary import build_completeness, merge_records

router = APIRouter(tags=["health-summary"])

doctor_only = require_role(UserRole.doctor)
patient_only = require_role(UserRole.patient)
needs_feature = require_feature("summary")


# ---------- helpers ----------
def _get_patient(db, actor, patient_id) -> User:
    p = (scoped_query(db, User, actor)
         .filter(User.id == patient_id, User.role == UserRole.patient).first())
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found in your practice")
    return p


def _store_record(db, actor, patient, payload: RecordCreate) -> MedicalRecord:
    rec = MedicalRecord(practice_id=actor.practice_id, patient_id=patient.id,
                        uploaded_by=actor.id, source_type=payload.source_type,
                        title=payload.title, data=json.dumps(payload.data))
    db.add(rec)
    db.commit()
    db.refresh(rec)
    write_audit(db, actor=actor, action_type="record.upload", data_accessed=f"patient:{patient.id}")
    return rec


def _generate(db, actor, patient) -> HealthSummary:
    if not has_consent(db, patient_id=patient.id, practice_id=patient.practice_id,
                       consent_type="ai_processing"):
        raise HTTPException(status_code=403,
                            detail="AI processing consent required before generating a summary.")

    records = (scoped_query(db, MedicalRecord, actor)
               .filter(MedicalRecord.patient_id == patient.id).all())
    parsed = [json.loads(r.data) for r in records]
    merged = merge_records(parsed)

    meds = (scoped_query(db, Medication, actor)
            .filter(Medication.patient_id == patient.id, Medication.is_active.is_(True)).all())
    med_dicts = [{"name_generic": m.name_generic, "dosage": m.dosage, "frequency": m.frequency}
                 for m in meds]

    patient_snap = ai.generate_health_summary(merged=merged, medications=med_dicts, audience="patient")
    clinician_snap = ai.generate_health_summary(merged=merged, medications=med_dicts, audience="doctor")
    completeness = build_completeness(merged, med_dicts)

    row = db.query(HealthSummary).filter(HealthSummary.patient_id == patient.id).first()
    if row is None:
        row = HealthSummary(practice_id=patient.practice_id, patient_id=patient.id)
        db.add(row)
    row.generated_by = actor.id
    row.patient_snapshot = json.dumps(patient_snap)
    row.clinician_snapshot = json.dumps(clinician_snap)
    row.completeness = json.dumps(completeness)
    row.source_record_count = len(records)
    row.generated_at = utcnow()
    db.commit()
    db.refresh(row)
    write_audit(db, actor=actor, action_type="summary.generate", data_accessed=f"patient:{patient.id}")
    return row


def _summary_out(row: HealthSummary, audience: str) -> HealthSummaryOut:
    snap = row.patient_snapshot if audience == "patient" else row.clinician_snapshot
    return HealthSummaryOut(patient_id=row.patient_id, snapshot=json.loads(snap),
                            completeness=json.loads(row.completeness),
                            source_record_count=row.source_record_count,
                            last_updated=row.generated_at)


def _require_summary(db, actor, patient_id) -> HealthSummary:
    row = (scoped_query(db, HealthSummary, actor)
           .filter(HealthSummary.patient_id == patient_id).first())
    if not row:
        raise HTTPException(status_code=404, detail="No summary yet. Generate one first.")
    return row


# ---------- records ----------
@router.post("/me/records", response_model=RecordOut, status_code=201)
def patient_upload(payload: RecordCreate, db: Session = Depends(get_db),
                   patient: User = Depends(patient_only), _=Depends(needs_feature)):
    return _store_record(db, patient, patient, payload)


@router.post("/patients/{patient_id}/records", response_model=RecordOut, status_code=201)
def doctor_upload(patient_id: str, payload: RecordCreate, db: Session = Depends(get_db),
                  doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    patient = _get_patient(db, doctor, patient_id)
    return _store_record(db, doctor, patient, payload)


@router.get("/me/records", response_model=list[RecordOut])
def patient_records(db: Session = Depends(get_db), patient: User = Depends(patient_only),
                    _=Depends(needs_feature)):
    return (scoped_query(db, MedicalRecord, patient)
            .filter(MedicalRecord.patient_id == patient.id)
            .order_by(MedicalRecord.created_at).all())


@router.get("/patients/{patient_id}/records", response_model=list[RecordOut])
def doctor_records(patient_id: str, db: Session = Depends(get_db),
                   doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    _get_patient(db, doctor, patient_id)
    return (scoped_query(db, MedicalRecord, doctor)
            .filter(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.created_at).all())


# ---------- generate ----------
@router.post("/me/health-summary/generate", response_model=HealthSummaryOut)
def patient_generate(db: Session = Depends(get_db), patient: User = Depends(patient_only),
                     _=Depends(needs_feature)):
    return _summary_out(_generate(db, patient, patient), "patient")


@router.post("/patients/{patient_id}/health-summary/generate", response_model=HealthSummaryOut)
def doctor_generate(patient_id: str, db: Session = Depends(get_db),
                    doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    patient = _get_patient(db, doctor, patient_id)
    return _summary_out(_generate(db, doctor, patient), "doctor")


# ---------- view ----------
@router.get("/me/health-summary", response_model=HealthSummaryOut)
def patient_view(db: Session = Depends(get_db), patient: User = Depends(patient_only),
                 _=Depends(needs_feature)):
    write_audit(db, actor=patient, action_type="summary.view", data_accessed="self")
    return _summary_out(_require_summary(db, patient, patient.id), "patient")


@router.get("/patients/{patient_id}/health-summary", response_model=HealthSummaryOut)
def doctor_view(patient_id: str, db: Session = Depends(get_db),
                doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    _get_patient(db, doctor, patient_id)
    write_audit(db, actor=doctor, action_type="summary.view", data_accessed=f"patient:{patient_id}")
    return _summary_out(_require_summary(db, doctor, patient_id), "doctor")


# ---------- PDF ----------
def _pdf_response(patient: User, row: HealthSummary, audience: str) -> Response:
    snap = json.loads(row.patient_snapshot if audience == "patient" else row.clinician_snapshot)
    data = pdf.render_snapshot_pdf(patient_name=patient.full_name, snapshot=snap,
                                   completeness=json.loads(row.completeness),
                                   last_updated=row.generated_at, audience=audience)
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="health-snapshot.pdf"'})


@router.get("/me/health-summary/pdf")
def patient_pdf(db: Session = Depends(get_db), patient: User = Depends(patient_only),
                _=Depends(needs_feature)):
    row = _require_summary(db, patient, patient.id)
    write_audit(db, actor=patient, action_type="summary.export_pdf", data_accessed="self")
    return _pdf_response(patient, row, "patient")


@router.get("/patients/{patient_id}/health-summary/pdf")
def doctor_pdf(patient_id: str, db: Session = Depends(get_db),
               doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    patient = _get_patient(db, doctor, patient_id)
    row = _require_summary(db, doctor, patient_id)
    write_audit(db, actor=doctor, action_type="summary.export_pdf", data_accessed=f"patient:{patient_id}")
    return _pdf_response(patient, row, "doctor")


# ---------- share ----------
@router.post("/patients/{patient_id}/health-summary/share", response_model=ShareOut, status_code=201)
def share_summary(patient_id: str, payload: ShareCreate, db: Session = Depends(get_db),
                  doctor: User = Depends(doctor_only), _=Depends(needs_feature)):
    _get_patient(db, doctor, patient_id)
    _require_summary(db, doctor, patient_id)
    token = secrets.token_urlsafe(32)
    share = SummaryShare(practice_id=doctor.practice_id, patient_id=patient_id,
                         created_by=doctor.id, token=token, shared_with=payload.shared_with,
                         expires_at=utcnow() + timedelta(days=payload.expires_in_days))
    db.add(share)
    db.commit()
    db.refresh(share)
    write_audit(db, actor=doctor, action_type="summary.share", data_accessed=f"patient:{patient_id}")
    return ShareOut(token=token, share_url=f"/shared/health-summary/{token}",
                    shared_with=share.shared_with, expires_at=share.expires_at)


@router.get("/shared/health-summary/{token}", response_model=HealthSummaryOut)
def view_shared(token: str, db: Session = Depends(get_db)):
    """Read-only access for an outside provider via a tokenized link (no login)."""
    share = db.query(SummaryShare).filter(SummaryShare.token == token).first()
    if not share:
        raise HTTPException(status_code=404, detail="Invalid share link")
    expires_at = share.expires_at
    if expires_at.tzinfo is None:  # DB round-trips as naive UTC
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < utcnow():
        raise HTTPException(status_code=410, detail="Share link has expired")
    row = db.query(HealthSummary).filter(HealthSummary.patient_id == share.patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Summary no longer available")
    write_audit(db, actor=None, action_type="summary.view_shared",
                data_accessed=f"patient:{share.patient_id}", detail=f"shared_with={share.shared_with}",
                practice_id=share.practice_id)
    # Outside providers receive the clinician view.
    return _summary_out(row, "doctor")
