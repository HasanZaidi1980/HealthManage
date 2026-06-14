"""Doctor-facing patient roster lookup (tenant-scoped).

Doctors need to discover patients in their practice to open records. Admins use
/admin/users for account management; this is the clinical-side read.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import write_audit
from app.core.deps import require_role, scoped_query
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas import UserOut

router = APIRouter(prefix="/patients", tags=["patients"])
doctor_only = require_role(UserRole.doctor)


@router.get("", response_model=list[UserOut])
def list_patients(db: Session = Depends(get_db), doctor: User = Depends(doctor_only)):
    return (scoped_query(db, User, doctor)
            .filter(User.role == UserRole.patient, User.is_active.is_(True))
            .order_by(User.full_name).all())


@router.get("/{patient_id}", response_model=UserOut)
def get_patient(patient_id: str, db: Session = Depends(get_db), doctor: User = Depends(doctor_only)):
    p = (scoped_query(db, User, doctor)
         .filter(User.id == patient_id, User.role == UserRole.patient).first())
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found in your practice")
    write_audit(db, actor=doctor, action_type="patient.view", data_accessed=str(patient_id))
    return p
