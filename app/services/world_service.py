from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models import Contract, ContractSource, ContractStatus, DailyReport, Notification, NotificationType, Sector, Station, WorldEvent
from app.services.admin_definitions import (
    contract_template_definitions,
    event_definitions,
    get_balance_number,
    module_definitions_map,
    resource_definitions_map,
    specialization_definitions_map,
)
from app.services.utils import change_resource, inventory_map


settings = get_settings()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def station_capacity(db: Session, station: Station) -> dict[str, float]:
    module_defs = module_definitions_map(db)
    values = {
        "energy_supply": 12.0,
        "storage": 100.0,
        "repair_capacity": 4.0,
        "trade_bonus": 0.0,
        "crew_capacity": 5.0,
        "automation": 0.0,
        "data_output": 2.0,
        "insight_gain": 0.25,
        "contract_slots": 2.0,
    }
    for module in station.modules:
        definition = module_defs.get(module.module_key)
        if not definition:
            continue
        for effect, amount in dict(definition.get("base_effect", {})).items():
            values[effect] = values.get(effect, 0.0) + float(amount) * module.level
    return values


def process_station_until(db: Session, station: Station, now: datetime) -> dict[str, object]:
    now = _as_utc(now)
    station.last_processed_at = _as_utc(station.last_processed_at)
    cap = timedelta(hours=settings.offline_progress_cap_hours)
    elapsed = min(now - station.last_processed_at, cap)
    ticks = int(elapsed.total_seconds() // settings.world_tick_seconds)
    if ticks <= 0:
        return {"profit": 0, "resources": {}, "completed_contracts": 0, "issues": [], "headline": "Изменений пока нет."}

    capacities = station_capacity(db, station)
    module_defs = module_definitions_map(db)
    specialization_defs = specialization_definitions_map(db)
    specialization = specialization_defs.get(station.specialization, {"throughput_multiplier": 1.0, "focus_resource": "fuel"})
    resources = inventory_map(station)
    energy_demand = sum(max(0, -float(module_defs.get(module.module_key, {}).get("energy_delta", 0)) * module.level) for module in station.modules)
    energy_supply = capacities["energy_supply"] + resources.get("energy", 0) * 0.02
    crew_available = resources.get("crew", 0) + capacities["crew_capacity"]
    storage_pressure = max(0, sum(resources.values()) - capacities["storage"]) / max(capacities["storage"], 1)
    power_ratio = min(1.0, energy_supply / max(energy_demand, 1))
    crew_ratio = min(1.0, crew_available / max(len(station.modules) * 1.5, 1))
    storage_ratio = max(0.6, 1.0 - storage_pressure * 0.35)
    automation_bonus = 1 + capacities["automation"]
    specialization_bonus = float(specialization.get("throughput_multiplier", 1.0))
    efficiency = max(0.35, power_ratio * crew_ratio * storage_ratio * automation_bonus * specialization_bonus)
    station.efficiency = round(efficiency, 3)

    focus_resource = str(specialization.get("focus_resource", "fuel"))
    credit_gain = ticks * (station.throughput * 2.0 * efficiency)
    fuel_gain = ticks * (0.7 if focus_resource == "fuel" else 0.35)
    parts_gain = ticks * (0.55 if focus_resource == "parts" or any(m.module_key == "repair_bay" for m in station.modules) else 0.25)
    data_gain = ticks * ((capacities["data_output"] * 0.22) if focus_resource == "data" or any(m.module_key == "data_core" for m in station.modules) else 0.2)
    alloy_gain = ticks * (0.35 if any(m.module_key == "warehouse" for m in station.modules) else 0.15)
    insight_gain = ticks * capacities["insight_gain"] * (1.2 if focus_resource == "data" else 1.0) * 0.1
    energy_change = ticks * max(-1.5, (capacities["energy_supply"] - energy_demand) * 0.08)

    change_resource(station, "credits", credit_gain)
    change_resource(station, "fuel", fuel_gain)
    change_resource(station, "parts", parts_gain)
    change_resource(station, "data", data_gain)
    change_resource(station, "alloy", alloy_gain)
    change_resource(station, "insight", insight_gain)
    change_resource(station, "energy", energy_change)
    station.reputation = round(min(100, station.reputation + ticks * 0.03 * efficiency), 2)
    station.stability = round(max(55, min(100, station.stability + (efficiency - 0.8) * ticks * 0.08)), 2)
    station.last_processed_at = now

    bottlenecks = []
    if power_ratio < 0.95:
        bottlenecks.append("Power")
    if crew_ratio < 0.95:
        bottlenecks.append("Crew")
    if storage_ratio < 0.95:
        bottlenecks.append("Storage")

    summary = {
        "profit": round(credit_gain, 2),
        "resources": {
            "fuel": round(fuel_gain, 2),
            "parts": round(parts_gain, 2),
            "data": round(data_gain, 2),
            "alloy": round(alloy_gain, 2),
            "insight": round(insight_gain, 2),
        },
        "completed_contracts": 0,
        "issues": bottlenecks,
        "headline": "Станция завершила автономный цикл.",
    }

    report_interval = int(get_balance_number(db, "report_interval_seconds", 60))
    if elapsed.total_seconds() >= report_interval:
        db.add(DailyReport(station=station, started_at=now - elapsed, ended_at=now, summary=summary))
    return summary


def process_due_stations(db: Session) -> int:
    now = datetime.now(UTC)
    stations = db.scalars(select(Station).options(joinedload(Station.modules), joinedload(Station.inventories))).unique().all()
    count = 0
    for station in stations:
        station.last_processed_at = _as_utc(station.last_processed_at)
        if (now - station.last_processed_at).total_seconds() >= settings.world_tick_seconds:
            process_station_until(db, station, now)
            count += 1
    return count


def _tick_fraction(reference_seconds: float) -> float:
    if reference_seconds <= 0:
        return 1.0
    return max(0.0, min(1.0, settings.world_tick_seconds / reference_seconds))


def _sanitize_market_price(value: float, minimum: float, maximum: float, fallback: float) -> float:
    if not math.isfinite(value) or value <= 0:
        return fallback
    return min(maximum, max(minimum, value))


def _sanitize_market_history(history: list[float] | None, minimum: float, maximum: float, fallback: float) -> list[float]:
    cleaned: list[float] = []
    for item in history or []:
        try:
            value = float(item)
        except (TypeError, ValueError):
            continue
        cleaned.append(round(_sanitize_market_price(value, minimum, maximum, fallback), 2))
    return cleaned[-19:]


def refresh_market(db: Session) -> None:
    drift_min = get_balance_number(db, "market_price_drift_min", -0.04)
    drift_max = get_balance_number(db, "market_price_drift_max", 0.04)
    mean_reversion_per_minute = get_balance_number(db, "market_mean_reversion_per_minute", 0.25)
    floor_multiplier = get_balance_number(db, "market_price_floor_multiplier", 0.35)
    cap_multiplier = get_balance_number(db, "market_price_cap_multiplier", 6.0)
    event_multiplier_cap = get_balance_number(db, "market_event_multiplier_cap", 3.0)
    tick_fraction = _tick_fraction(60.0)
    resource_map = resource_definitions_map(db)
    sectors = db.scalars(select(Sector).options(joinedload(Sector.market_states), joinedload(Sector.world_events))).unique().all()
    now = datetime.now(UTC)
    for sector in sectors:
        active_events = [event for event in sector.world_events if _as_utc(event.ends_at) >= now]
        for market in sector.market_states:
            base_price = max(1.0, float(resource_map.get(market.resource, {}).get("base_price", market.price or 1.0) or 1.0))
            multiplier = 1.0
            for event in active_events:
                try:
                    effect = float(event.market_effects.get(market.resource, 1.0))
                except (TypeError, ValueError):
                    effect = 1.0
                multiplier *= max(0.25, effect)
            multiplier = min(max(1.0 / max(event_multiplier_cap, 1.0), multiplier), max(event_multiplier_cap, 1.0))
            fair_price = base_price * multiplier
            minimum_price = max(1.0, base_price * max(0.05, floor_multiplier) * min(1.0, multiplier))
            maximum_price = max(minimum_price, base_price * max(floor_multiplier + 0.1, cap_multiplier) * max(1.0, multiplier))
            previous_price = _sanitize_market_price(float(market.price), minimum_price, maximum_price, fair_price)
            drift = random.uniform(drift_min, drift_max) * tick_fraction
            drifted_price = previous_price * max(0.1, 1 + drift)
            reversion = max(0.0, mean_reversion_per_minute) * tick_fraction
            new_price = drifted_price + (fair_price - drifted_price) * reversion
            new_price = round(_sanitize_market_price(new_price, minimum_price, maximum_price, fair_price), 2)
            history = _sanitize_market_history(market.history, minimum_price, maximum_price, fair_price)
            history.append(new_price)
            market.trend = round(new_price - previous_price, 2)
            market.price = new_price
            market.history = history


def _conditions_match(db: Session, sector: Sector, conditions: dict[str, object]) -> bool:
    player_count = db.scalar(select(func.count(Station.id)).where(Station.sector_id == sector.id)) or 0
    all_rules = list(conditions.get("all", [])) if isinstance(conditions, dict) else []
    for rule in all_rules:
        field = rule.get("field")
        op = rule.get("op")
        value = rule.get("value")
        actual = None
        if field == "sector_player_count":
            actual = player_count
        if actual is None:
            continue
        if op == ">=" and not actual >= value:
            return False
        if op == ">" and not actual > value:
            return False
        if op == "==" and not actual == value:
            return False
    return True


def maybe_spawn_event(db: Session) -> WorldEvent | None:
    sector = db.scalar(select(Sector))
    spawn_chance = min(1.0, max(0.0, get_balance_number(db, "world_event_spawn_chance", 0.35)))
    per_tick_spawn_chance = 1 - (1 - spawn_chance) ** _tick_fraction(60.0)
    if not sector or random.random() > per_tick_spawn_chance:
        return None
    now = datetime.now(UTC)
    definitions = [item for item in event_definitions(db) if item.get("enabled", True)]
    definitions = [item for item in definitions if _conditions_match(db, sector, dict(item.get("conditions", {})))]
    filtered_definitions: list[dict[str, object]] = []
    for item in definitions:
        key = str(item.get("key", ""))
        cooldown_minutes = max(0, int(item.get("cooldown_minutes", 0) or 0))
        matching_events = [event for event in sector.world_events if event.key == key]
        if any(_as_utc(event.ends_at) >= now for event in matching_events):
            continue
        cooldown_boundary = now - timedelta(minutes=cooldown_minutes)
        if cooldown_minutes and any(_as_utc(event.ends_at) >= cooldown_boundary for event in matching_events):
            continue
        filtered_definitions.append(item)
    definitions = filtered_definitions
    if not definitions:
        return None
    weights = [max(0.0, float(item.get("weight", 1.0) or 1.0)) for item in definitions]
    template = random.choices(definitions, weights=weights, k=1)[0]
    event = WorldEvent(
        sector_id=sector.id,
        key=str(template["key"]),
        title=str(template["title"]),
        description=str(template["long_description"]),
        market_effects=dict(template.get("market_effects", {})),
        starts_at=now,
        ends_at=now + timedelta(minutes=int(template.get("duration_minutes", 60))),
    )
    db.add(event)
    for station in db.scalars(select(Station)).all():
        db.add(
            Notification(
                user_id=station.owner_id,
                type=NotificationType.market,
                title=event.title,
                message=event.description[:180],
                payload={"event_id": event.id, "effects": event.market_effects},
            )
        )
    return event


def ensure_npc_contracts(db: Session, sector_id: str, desired_open: int | None = None) -> None:
    if desired_open is None:
        desired_open = int(get_balance_number(db, "npc_contract_target_open", 8))
    open_count = db.scalar(
        select(func.count(Contract.id)).where(Contract.sector_id == sector_id, Contract.source == ContractSource.npc, Contract.status == ContractStatus.open)
    )
    missing = max(0, desired_open - int(open_count or 0))
    now = datetime.now(UTC)
    templates = [item for item in contract_template_definitions(db) if item.get("enabled", True)]
    for template in random.sample(templates, k=min(missing, len(templates))):
        db.add(
            Contract(
                sector_id=sector_id,
                source=ContractSource.npc,
                status=ContractStatus.open,
                contract_type=str(template["contract_type"]),
                title=str(template["title"]),
                resource=str(template["resource"]),
                quantity=float(template["quantity"]),
                reward_credits=float(template["reward_credits"]),
                reward_reputation=float(template.get("reward_reputation", 0)),
                expires_at=now + timedelta(hours=8),
            )
        )


def world_tick(db: Session) -> dict[str, int]:
    station_count = process_due_stations(db)
    refresh_market(db)
    event = maybe_spawn_event(db)
    sector = db.scalar(select(Sector))
    if sector:
        ensure_npc_contracts(db, sector.id)
    db.commit()
    return {"stations_processed": station_count, "event_spawned": 1 if event else 0}
