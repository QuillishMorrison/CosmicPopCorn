from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import MarketTransaction, User
from app.schemas.game import MarketStateView, MarketTradeRequest
from app.services.market_service import execute_market_trade, get_market_state
from app.services.station_service import get_station_for_user

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/state", response_model=list[MarketStateView])
def state(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[MarketStateView]:
    station = get_station_for_user(db, current_user.id)
    return [MarketStateView.model_validate(item) for item in get_market_state(db, station.sector_id)]


@router.get("/history")
def history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[dict[str, object]]:
    station = get_station_for_user(db, current_user.id)
    items = db.scalars(
        select(MarketTransaction)
        .where(MarketTransaction.station_id == station.id)
        .order_by(MarketTransaction.created_at.desc())
    ).all()
    return [
        {
            "id": tx.id,
            "resource": tx.resource,
            "side": tx.side,
            "quantity": tx.quantity,
            "unit_price": tx.unit_price,
            "total_price": tx.total_price,
            "created_at": tx.created_at.isoformat(),
        }
        for tx in items[:20]
    ]


@router.post("/buy")
def buy(
    payload: MarketTradeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    station = get_station_for_user(db, current_user.id)
    try:
        execute_market_trade(db, station, payload.resource, payload.quantity, "buy")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return {"message": "Покупка завершена."}


@router.post("/sell")
def sell(
    payload: MarketTradeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    station = get_station_for_user(db, current_user.id)
    try:
        execute_market_trade(db, station, payload.resource, payload.quantity, "sell")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return {"message": "Продажа завершена."}
