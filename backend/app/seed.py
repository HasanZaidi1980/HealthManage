"""Synthetic seed: 2 practices, users, and a sample medication list.
Run:  python -m app.seed   (SYNTHETIC data only)"""
import json
from datetime import date
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.consent import Consent
from app.models.enums import SubscriptionTier, UserRole
from app.models.medication import Medication
from app.models.practice import Practice
from app.models.record import MedicalRecord
from app.models.user import User
from app.services import ai
import app.models  # noqa: F401


def _u(p, email, name, role):
    return User(practice_id=p.id, email=email, hashed_password=hash_password("password123"),
                full_name=name, role=role)


def _med(p, patient, doctor, generic, brand, dosage, freq):
    return Medication(
        practice_id=p.id, patient_id=patient.id, prescribed_by=doctor.id,
        name_generic=generic, name_brand=brand, dosage=dosage, frequency=freq,
        prescribing_provider=doctor.full_name, start_date=date(2026, 1, 15),
        plain_language_purpose=ai.generate_medication_purpose(
            generic=generic, brand=brand, dosage=dosage, frequency=freq, audience="patient"),
        clinical_indication=ai.generate_medication_purpose(
            generic=generic, brand=brand, dosage=dosage, frequency=freq, audience="doctor"))


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Practice).first():
            print("Data already present — skipping seed.")
            return
        a = Practice(name="Katy Family Clinic", subscription_tier=SubscriptionTier.professional)
        b = Practice(name="Houston Heart Associates", subscription_tier=SubscriptionTier.starter)
        db.add_all([a, b]); db.flush()

        admin_a = _u(a, "admin@katyclinic.example.com", "Ava Admin", UserRole.admin)
        doc_a = _u(a, "dr.reyes@katyclinic.example.com", "Dr. Marco Reyes", UserRole.doctor)
        pat_a = _u(a, "patient.jordan@katyclinic.example.com", "Jordan Lee", UserRole.patient)
        db.add_all([admin_a, doc_a, pat_a,
                    _u(b, "admin@houstonheart.example.com", "Ben Admin", UserRole.admin),
                    _u(b, "dr.shah@houstonheart.example.com", "Dr. Nina Shah", UserRole.doctor)])
        db.flush()

        # Sample meds (warfarin + aspirin trip the interaction flag)
        db.add_all([
            _med(a, pat_a, doc_a, "warfarin", "Coumadin", "5 mg", "once daily"),
            _med(a, pat_a, doc_a, "aspirin", "Bayer", "81 mg", "once daily"),
            _med(a, pat_a, doc_a, "metformin", "Glucophage", "500 mg", "twice daily"),
        ])
        # Sample source record for Jordan (simulated EHR import as structured JSON)
        db.add(MedicalRecord(
            practice_id=a.id, patient_id=pat_a.id, uploaded_by=doc_a.id,
            source_type="json", title="Imported EHR Summary",
            data=json.dumps({
                "conditions": [
                    {"name": "Type 2 Diabetes", "status": "active", "since": "2021"},
                    {"name": "Hypertension", "status": "active", "since": "2022"},
                ],
                "allergies": [
                    {"substance": "Penicillin", "type": "drug", "reaction": "hives"},
                ],
                "labs": [
                    {"name": "HbA1c", "value": "7.4%", "date": "2026-05-02", "flag": "high"},
                    {"name": "Blood Pressure", "value": "138/86", "date": "2026-05-02", "flag": "borderline"},
                ],
                "imaging": [
                    {"name": "Chest X-ray", "date": "2026-03-11", "result": "normal", "flag": "normal"},
                ],
            })))
        # Patient consents to AI processing so the interactions view works in demo
        db.add(Consent(practice_id=a.id, patient_id=pat_a.id,
                       consent_type="ai_processing", version="v1", granted=True))
        db.commit()
        print("Seeded 2 practices, 5 users, 3 meds, 1 record, 1 consent. Password: password123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
