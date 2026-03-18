from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import PlayerTransfer, Station, User
from app.schemas.common import MessageResponse
from app.schemas.game import TransferRequest
from app.services.station_service import get_station_for_user
from app.services.utils import change_resource, inventory_map

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.post("/send", response_model=MessageResponse)
def send_resources(
    payload: TransferRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> MessageResponse:
    station = get_station_for_user(db, current_user.id)
    target = db.get(Station, payload.target_station_id)
    if not target or target.sector_id != station.sector_id:
        raise HTTPException(status_code=404, detail="Target station unavailable.")
    if inventory_map(station).get(payload.resource, 0) < payload.amount:
        raise HTTPException(status_code=400, detail="Not enough resources.")
    change_resource(station, payload.resource, -payload.amount)
    change_resource(target, payload.resource, payload.amount)
    db.add(
        PlayerTransfer(
            from_station_id=station.id,
            to_station_id=target.id,
            resource=payload.resource,
            amount=payload.amount,
            note=payload.note,
        )
    )
    db.commit()
    return MessageResponse(message="Перевод отправлен.")


@router.get("/mine")
def my_transfers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict[str, object]]:
    station = get_station_for_user(db, current_user.id)
    items = db.scalars(
        select(PlayerTransfer)
        .where((PlayerTransfer.from_station_id == station.id) | (PlayerTransfer.to_station_id == station.id))
        .order_by(PlayerTransfer.created_at.desc())
    ).all()
    return [
        {
            "id": transfer.id,
            "from_station_id": transfer.from_station_id,
            "to_station_id": transfer.to_station_id,
            "resource": transfer.resource,
            "amount": transfer.amount,
            "note": transfer.note,
            "created_at": transfer.created_at.isoformat(),
        }
        for transfer in items
    ]
