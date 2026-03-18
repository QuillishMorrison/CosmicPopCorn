from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Notification, User
from app.schemas.common import MessageResponse
from app.schemas.game import NotificationView

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=list[NotificationView])
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[NotificationView]:
    items = db.scalars(
        select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
    ).all()
    return [NotificationView.model_validate(item) for item in items[:30]]


@router.post("/{notification_id}/read", response_model=MessageResponse)
def mark_read(
    notification_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> MessageResponse:
    item = db.get(Notification, notification_id)
    if not item or item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification unavailable.")
    item.read_at = datetime.now(UTC)
    db.commit()
    return MessageResponse(message="Уведомление отмечено как прочитанное.")
