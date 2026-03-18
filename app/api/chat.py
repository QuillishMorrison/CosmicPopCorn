from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.game import ChatMessageView, ChatSendRequest, ChatThreadView
from app.services.chat_service import (
    list_direct_messages,
    list_global_messages,
    list_threads,
    send_direct_message,
    send_global_message,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/global", response_model=list[ChatMessageView])
def global_chat(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[ChatMessageView]:
    return list_global_messages(db)


@router.post("/global", response_model=ChatMessageView)
def post_global(
    payload: ChatSendRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> ChatMessageView:
    item = send_global_message(db, current_user, payload.body)
    db.commit()
    return item


@router.get("/threads", response_model=list[ChatThreadView])
def threads(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[ChatThreadView]:
    return list_threads(db, current_user)


@router.get("/direct/{user_id}", response_model=list[ChatMessageView])
def direct_chat(
    user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[ChatMessageView]:
    return list_direct_messages(db, current_user.id, user_id)


@router.post("/direct/{user_id}", response_model=ChatMessageView)
def post_direct(
    user_id: str,
    payload: ChatSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatMessageView:
    item = send_direct_message(db, current_user, user_id, payload.body)
    db.commit()
    return item
