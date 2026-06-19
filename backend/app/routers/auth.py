"""Auth endpoints: bootstrap a practice, log in, read current user."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.audit import write_audit
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.enums import UserRole
from app.models.practice import Practice
from app.models.user import User
from app.schemas import LoginRequest, RegisterPracticeRequest, TokenResponse, UserOut
from app.schemas import PracticeOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register-practice", response_model=TokenResponse, status_code=201)
def register_practice(payload: RegisterPracticeRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.admin_email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    practice = Practice(name=payload.practice_name, subscription_tier=payload.subscription_tier)
    db.add(practice)
    db.flush()
    admin = User(practice_id=practice.id, email=payload.admin_email,
                 hashed_password=hash_password(payload.admin_password),
                 full_name=payload.admin_full_name, role=UserRole.admin)
    db.add(admin)
    db.commit()
    db.refresh(admin)
    write_audit(db, actor=admin, action_type="practice.register", data_accessed="practice")
    token = create_access_token(user_id=admin.id, role=admin.role.value, practice_id=admin.practice_id)
    return TokenResponse(access_token=token, role=admin.role, practice_id=admin.practice_id)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    write_audit(db, actor=user, action_type="auth.login")
    token = create_access_token(user_id=user.id, role=user.role.value, practice_id=user.practice_id)
    return TokenResponse(access_token=token, role=user.role, practice_id=user.practice_id)


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


@router.get("/me/practice", response_model=PracticeOut)
def my_practice(current: User = Depends(get_current_user)):
    """Practice info for the signed-in user (name/tier). No PHI."""
    return current.practice
