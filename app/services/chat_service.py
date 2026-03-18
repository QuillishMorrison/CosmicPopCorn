from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import ChatMessage, Station, User
from app.schemas.game import ChatMessageView, ChatThreadView


def _clean_body(body: str) -> str:
    cleaned = " ".join(body.split()).strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Сообщение пустое.")
    return cleaned


def _enforce_chat_rate_limit(db: Session, sender_user_id: str) -> None:
    threshold = datetime.now(UTC) - timedelta(seconds=2)
    latest = db.scalar(
        select(ChatMessage)
        .where(ChatMessage.sender_user_id == sender_user_id, ChatMessage.created_at >= threshold)
        .order_by(ChatMessage.created_at.desc())
    )
    if latest:
        raise HTTPException(status_code=429, detail="Слишком часто. Подождите пару секунд.")


def serialize_message(db: Session, item: ChatMessage) -> ChatMessageView:
    sender = db.get(User, item.sender_user_id)
    return ChatMessageView(
        id=item.id,
        sender_user_id=item.sender_user_id,
        sender_username=sender.username if sender else "unknown",
        recipient_user_id=item.recipient_user_id,
        body=item.body,
        created_at=item.created_at,
    )


def list_global_messages(db: Session, limit: int = 40) -> list[ChatMessageView]:
    items = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.recipient_user_id.is_(None))
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    ).all()
    return [serialize_message(db, item) for item in reversed(items)]


def list_direct_messages(db: Session, current_user_id: str, other_user_id: str, limit: int = 40) -> list[ChatMessageView]:
    items = db.scalars(
        select(ChatMessage)
        .where(
            or_(
                (ChatMessage.sender_user_id == current_user_id) & (ChatMessage.recipient_user_id == other_user_id),
                (ChatMessage.sender_user_id == other_user_id) & (ChatMessage.recipient_user_id == current_user_id),
            )
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    ).all()
    return [serialize_message(db, item) for item in reversed(items)]


def list_threads(db: Session, current_user: User) -> list[ChatThreadView]:
    current_station = db.scalar(select(Station).where(Station.owner_id == current_user.id))
    candidates = db.scalars(select(User).order_by(User.username.asc())).all()

    if current_station:
        sector_owner_ids = {
            station.owner_id
            for station in db.scalars(select(Station).where(Station.sector_id == current_station.sector_id)).all()
        }
        candidates = [user for user in candidates if user.id in sector_owner_ids]

    threads: list[ChatThreadView] = []
    for user in candidates:
        if user.id == current_user.id:
            continue

        station = db.scalar(select(Station).where(Station.owner_id == user.id))
        latest = db.scalar(
            select(ChatMessage)
            .where(
                or_(
                    (ChatMessage.sender_user_id == current_user.id) & (ChatMessage.recipient_user_id == user.id),
                    (ChatMessage.sender_user_id == user.id) & (ChatMessage.recipient_user_id == current_user.id),
                )
            )
            .order_by(ChatMessage.created_at.desc())
        )
        threads.append(
            ChatThreadView(
                user_id=user.id,
                username=user.username,
                station_name=station.name if station else None,
                last_message=latest.body if latest else None,
                last_message_at=latest.created_at if latest else None,
                unread_count=0,
            )
        )

    return threads


def send_global_message(db: Session, current_user: User, body: str) -> ChatMessageView:
    _enforce_chat_rate_limit(db, current_user.id)
    item = ChatMessage(sender_user_id=current_user.id, recipient_user_id=None, body=_clean_body(body))
    db.add(item)
    db.flush()
    return serialize_message(db, item)


def send_direct_message(db: Session, current_user: User, recipient_user_id: str, body: str) -> ChatMessageView:
    if recipient_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя писать самому себе.")
    recipient = db.get(User, recipient_user_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Игрок недоступен.")

    _enforce_chat_rate_limit(db, current_user.id)
    item = ChatMessage(
        sender_user_id=current_user.id,
        recipient_user_id=recipient_user_id,
        body=_clean_body(body),
    )
    db.add(item)
    db.flush()
    return serialize_message(db, item)
