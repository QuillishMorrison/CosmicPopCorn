from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AuthAttempt, SecurityLog


def ensure_auth_allowed(db: Session, identity: str, ip_address: str, endpoint: str) -> None:
    now = datetime.now(UTC)
    windows = [
        (timedelta(minutes=5), 5, 60),
        (timedelta(minutes=15), 10, 300),
        (timedelta(hours=1), 20, 1800),
    ]
    max_retry_after = 0
    for window, limit, cooldown in windows:
        count = db.scalar(
            select(func.count(AuthAttempt.id)).where(
                AuthAttempt.created_at >= now - window,
                AuthAttempt.endpoint == endpoint,
                AuthAttempt.success.is_(False),
                (AuthAttempt.ip_address == ip_address) | (AuthAttempt.identity == identity),
            )
        )
        if count and count >= limit:
            max_retry_after = max(max_retry_after, cooldown)
    if max_retry_after:
        db.add(
            SecurityLog(
                user_id=None,
                event_type="auth_locked",
                severity="warning",
                ip_address=ip_address,
                detail={"identity": identity, "endpoint": endpoint, "retry_after": max_retry_after},
            )
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please wait before retrying.",
            headers={"Retry-After": str(max_retry_after)},
        )


def record_auth_attempt(db: Session, identity: str, ip_address: str, endpoint: str, success: bool) -> None:
    db.add(AuthAttempt(identity=identity, ip_address=ip_address, endpoint=endpoint, success=success))
    db.commit()
