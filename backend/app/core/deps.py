"""Dependencies enforcing auth, role, tenant, and tier — all server-side.

The tenant (`practice_id`) always comes from the verified JWT, never from
client input, so cross-tenant access is structurally prevented.
"""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.core.tiers import tier_has_feature
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=True)

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(creds.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise _CREDENTIALS_EXC
    except jwt.PyJWTError:
        raise _CREDENTIALS_EXC

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC
    if str(user.practice_id) != str(payload.get("practice_id")):
        raise _CREDENTIALS_EXC
    return user


def require_role(*roles: UserRole):
    allowed = {r.value for r in roles}

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Your role is not permitted to access this resource")
        return user

    return _checker


def require_feature(feature: str):
    def _checker(user: User = Depends(get_current_user)) -> User:
        if not tier_has_feature(user.practice.subscription_tier, feature):
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED,
                                detail=f"Feature '{feature}' is not included in your practice's plan")
        return user

    return _checker


def scoped_query(db: Session, model, user: User):
    """Query for `model` pre-filtered to the user's practice tenant."""
    return db.query(model).filter(model.practice_id == user.practice_id)
