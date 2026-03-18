from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MarketState, MarketTransaction, Station
from app.services.admin_definitions import get_balance_number, resource_definitions_map
from app.services.utils import change_resource, format_missing_resources, inventory_map


def get_market_state(db: Session, sector_id: str) -> list[MarketState]:
    return db.scalars(select(MarketState).where(MarketState.sector_id == sector_id).order_by(MarketState.id)).all()


def execute_market_trade(db: Session, station: Station, resource: str, quantity: float, side: str) -> None:
    if resource not in resource_definitions_map(db):
        raise ValueError("Ресурс недоступен на рынке.")

    market = db.scalar(select(MarketState).where(MarketState.sector_id == station.sector_id, MarketState.resource == resource))
    if not market:
        raise ValueError("Ресурс недоступен на рынке.")

    resources = inventory_map(station)
    market_terminal = next((module for module in station.modules if module.module_key == "market_terminal"), None)
    per_level = get_balance_number(db, "market_trade_bonus_per_level", 0.03)
    buy_floor = get_balance_number(db, "market_buy_discount_floor", 0.72)
    min_buy_multiplier = get_balance_number(db, "market_min_buy_multiplier", 0.92)
    sell_ratio = get_balance_number(db, "market_sell_bonus_ratio", 0.6)
    sell_spread = get_balance_number(db, "market_sell_spread", 0.18)
    max_sell_multiplier = get_balance_number(db, "market_max_sell_multiplier", 0.88)
    trade_bonus = (market_terminal.level if market_terminal else 0) * per_level
    base_total = quantity * market.price

    if side == "buy":
        buy_multiplier = max(min_buy_multiplier, buy_floor, 1 - trade_bonus)
        total = round(base_total * buy_multiplier, 2)
        if resources.get("credits", 0) < total:
            missing = format_missing_resources({"credits": total}, station)
            raise ValueError(f"Недостаточно ресурсов: {missing}")
        change_resource(station, "credits", -total)
        change_resource(station, resource, quantity)
        market.price = round(market.price * (1 + min(0.08, quantity / 1000)), 2)
    else:
        sell_multiplier = min(max_sell_multiplier, max(0.1, 1 - sell_spread + trade_bonus * sell_ratio))
        total = round(base_total * sell_multiplier, 2)
        if resources.get(resource, 0) < quantity:
            missing = format_missing_resources({resource: quantity}, station)
            raise ValueError(f"Недостаточно ресурсов: {missing}")
        change_resource(station, resource, -quantity)
        change_resource(station, "credits", total)
        market.price = round(max(1.0, market.price * (1 - min(0.06, quantity / 1200))), 2)

    history = (market.history or [])[-19:]
    history.append(market.price)
    market.history = history

    db.add(
        MarketTransaction(
            station_id=station.id,
            sector_id=station.sector_id,
            resource=resource,
            side=side,
            quantity=quantity,
            unit_price=round(total / quantity, 2),
            total_price=total,
        )
    )
