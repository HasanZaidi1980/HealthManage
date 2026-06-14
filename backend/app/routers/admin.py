"""Practice Admin endpoints: account management + billing, tenant-scoped.
No PHI access (admins never touch medication/record routes)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.audit import write_audit
from app.core.deps import require_role, scoped_query
from app.core.security import hash_password
from app.core.tiers import TIER_FEATURES, tier_limit
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas import CreateUserRequest, PracticeBilling, PracticeOut, UserOut

router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_role(UserRole.admin)


def _count_role(db, admin, role):
    return scoped_query(db, User, admin).filter(User.role == role).count()


def _create_user(db, admin, payload, role, limit_key):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    limit = tier_limit(admin.practice.subscription_tier, limit_key)
    if limit is not None and _count_role(db, admin, role) >= limit:
        raise HTTPException(status_code=402,
                            detail=f"Plan limit reached: {limit} {role.value} accounts. Upgrade to add more.")
    user = User(practice_id=admin.practice_id, email=payload.email,
                hashed_password=hash_password(payload.password),
                full_name=payload.full_name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    write_audit(db, actor=admin, action_type=f"{role.value}.create", data_accessed=str(user.id))
    return user


@router.post("/doctors", response_model=UserOut, status_code=201)
def create_doctor(payload: CreateUserRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    return _create_user(db, admin, payload, UserRole.doctor, "max_doctors")


@router.post("/patients", response_model=UserOut, status_code=201)
def create_patient(payload: CreateUserRequest, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    return _create_user(db, admin, payload, UserRole.patient, "max_patients")


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    return scoped_query(db, User, admin).order_by(User.created_at).all()


@router.patch("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: str, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    user = scoped_query(db, User, admin).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found in your practice")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own admin account")
    user.is_active = False
    db.commit()
    db.refresh(user)
    write_audit(db, actor=admin, action_type="user.deactivate", data_accessed=str(user.id))
    return user


@router.get("/billing", response_model=PracticeBilling)
def billing(db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    tier = admin.practice.subscription_tier
    return PracticeBilling(practice=PracticeOut.model_validate(admin.practice),
                           features=sorted(TIER_FEATURES[tier]),
                           doctor_count=_count_role(db, admin, UserRole.doctor),
                           patient_count=_count_role(db, admin, UserRole.patient),
                           max_doctors=tier_limit(tier, "max_doctors"),
                           max_patients=tier_limit(tier, "max_patients"))
