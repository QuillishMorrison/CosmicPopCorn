from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import ContractSource, User
from app.schemas.common import MessageResponse
from app.schemas.game import ContractCreateRequest
from app.services.contract_service import (
    accept_contract,
    cancel_contract,
    create_player_contract,
    list_contracts,
    visible_npc_contracts_for_station,
)
from app.services.station_service import get_station_for_user

router = APIRouter(prefix="/contracts", tags=["contracts"])


def _serialize_contract(contract: object) -> dict[str, object]:
    return {
        "id": getattr(contract, "id"),
        "title": getattr(contract, "title"),
        "contract_type": getattr(contract, "contract_type"),
        "resource": getattr(contract, "resource"),
        "quantity": getattr(contract, "quantity"),
        "reward_credits": getattr(contract, "reward_credits"),
        "reward_reputation": getattr(contract, "reward_reputation"),
        "status": getattr(contract, "status").value,
        "source": getattr(contract, "source").value,
        "issuer_station_id": getattr(contract, "issuer_station_id"),
        "taker_station_id": getattr(contract, "taker_station_id"),
        "expires_at": getattr(contract, "expires_at").isoformat(),
    }


@router.get("/npc")
def npc_contracts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[dict[str, object]]:
    station = get_station_for_user(db, current_user.id)
    return [_serialize_contract(contract) for contract in visible_npc_contracts_for_station(db, station)]


@router.get("/player")
def player_contracts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[dict[str, object]]:
    station = get_station_for_user(db, current_user.id)
    return [_serialize_contract(contract) for contract in list_contracts(db, station.sector_id, ContractSource.player)]


@router.get("/mine")
def my_contracts(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[dict[str, object]]:
    station = get_station_for_user(db, current_user.id)
    items = [
        contract
        for contract in list_contracts(db, station.sector_id)
        if contract.issuer_station_id == station.id or contract.taker_station_id == station.id
    ]
    return [_serialize_contract(contract) for contract in items]


@router.post("/create")
def create_contract(
    payload: ContractCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> dict[str, object]:
    station = get_station_for_user(db, current_user.id)
    contract = create_player_contract(
        db,
        station,
        payload.title,
        payload.contract_type,
        payload.resource,
        payload.quantity,
        payload.reward_credits,
    )
    db.commit()
    db.refresh(contract)
    return _serialize_contract(contract)


@router.post("/{contract_id}/accept", response_model=MessageResponse)
def accept(
    contract_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> MessageResponse:
    station = get_station_for_user(db, current_user.id)
    accept_contract(db, station, contract_id)
    db.commit()
    return MessageResponse(message="Контракт выполнен.")


@router.post("/{contract_id}/cancel", response_model=MessageResponse)
def cancel(
    contract_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> MessageResponse:
    station = get_station_for_user(db, current_user.id)
    cancel_contract(db, station, contract_id)
    db.commit()
    return MessageResponse(message="Контракт отменён.")
