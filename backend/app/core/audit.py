from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.user import User


def write_audit(db: Session, *, actor: User | None, action_type: str,
                data_accessed: str | None = None, detail: str | None = None,
                practice_id=None) -> AuditLog:
    log = AuditLog(
        practice_id=practice_id or (actor.practice_id if actor else None),
        user_id=actor.id if actor else None,
        action_type=action_type, data_accessed=data_accessed, detail=detail)
    db.add(log)
    db.commit()
    return log
