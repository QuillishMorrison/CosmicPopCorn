from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Contract, ContractSource, ContractStatus, Notification, NotificationType, Station
from app.services.utils import change_resource, format_missing_resources, inventory_map


def list_contracts(db: Session, sector_id: str, source: ContractSource | None = None) -> list[Contract]:
    query = select(Contract).where(Contract.sector_id == sector_id)
    if source:
        query = query.where(Contract.source == source)
    return db.scalars(query.order_by(Contract.created_at.desc())).all()


def npc_contract_visibility_limit(station: Station) -> int:
    market_terminal = next((module for module in station.modules if module.module_key == "market_terminal"), None)
    level = market_terminal.level if market_terminal else 0
    if level >= 5:
        return 8
    if level >= 3:
        return 6
    if level >= 1:
        return 4
    return 2


def visible_npc_contracts_for_station(db: Session, station: Station) -> list[Contract]:
    return list_contracts(db, station.sector_id, ContractSource.npc)[: npc_contract_visibility_limit(station)]


def create_player_contract(
    db: Session,
    station: Station,
    title: str,
    contract_type: str,
    resource: str,
    quantity: float,
    reward_credits: float,
) -> Contract:
    if inventory_map(station).get(resource, 0) < quantity:
        missing = format_missing_resources(station, {resource: quantity})
        raise HTTPException(status_code=400, detail=f"Недостаточно ресурсов: {missing}")

    change_resource(station, resource, -quantity)
    contract = Contract(
        sector_id=station.sector_id,
        issuer_station_id=station.id,
        source=ContractSource.player,
        status=ContractStatus.open,
        contract_type=contract_type,
        title=title,
        resource=resource,
        quantity=quantity,
        reward_credits=reward_credits,
        reward_reputation=2,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
    )
    db.add(contract)
    return contract


def accept_contract(db: Session, station: Station, contract_id: str) -> Contract:
    contract = db.get(Contract, contract_id)
    if not contract or contract.status != ContractStatus.open:
        raise HTTPException(status_code=404, detail="Контракт недоступен.")

    if contract.source == ContractSource.npc and inventory_map(station).get(contract.resource, 0) < contract.quantity:
        missing = format_missing_resources(station, {contract.resource: contract.quantity})
        raise HTTPException(status_code=400, detail=f"Недостаточно ресурсов: {missing}")

    if contract.source == ContractSource.npc:
        change_resource(station, contract.resource, -contract.quantity)

    if contract.source == ContractSource.player:
        issuer = db.get(Station, contract.issuer_station_id) if contract.issuer_station_id else None
        if issuer and inventory_map(issuer).get("credits", 0) < contract.reward_credits:
            raise HTTPException(status_code=400, detail="Заказчик больше не может оплатить этот контракт.")
        if inventory_map(station).get(contract.resource, 0) < contract.quantity:
            missing = format_missing_resources(station, {contract.resource: contract.quantity})
            raise HTTPException(status_code=400, detail=f"Недостаточно ресурсов: {missing}")

        change_resource(station, contract.resource, -contract.quantity)
        if issuer:
            change_resource(issuer, contract.resource, contract.quantity)
            change_resource(issuer, "credits", -contract.reward_credits)
            db.add(
                Notification(
                    user_id=issuer.owner_id,
                    type=NotificationType.contract,
                    title="Контракт выполнен",
                    message=f"{station.name} выполнила контракт «{contract.title}».",
                    payload={"contract_id": contract.id},
                )
            )

    change_resource(station, "credits", contract.reward_credits)
    station.reputation = round(station.reputation + contract.reward_reputation, 2)
    contract.taker_station_id = station.id
    contract.status = ContractStatus.completed
    contract.accepted_at = datetime.now(UTC)
    contract.completed_at = datetime.now(UTC)
    return contract


def cancel_contract(db: Session, station: Station, contract_id: str) -> Contract:
    contract = db.get(Contract, contract_id)
    if not contract or contract.issuer_station_id != station.id:
        raise HTTPException(status_code=404, detail="Контракт недоступен.")
    if contract.status != ContractStatus.open:
        raise HTTPException(status_code=400, detail="Контракт уже нельзя отменить.")

    contract.status = ContractStatus.cancelled
    change_resource(station, contract.resource, contract.quantity)
    return contract
