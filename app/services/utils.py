from __future__ import annotations

from decimal import Decimal

from app.models import Inventory, Station


def inventory_map(station: Station) -> dict[str, float]:
    return {item.resource: float(item.amount) for item in station.inventories}


def ensure_inventory(station: Station, resource: str) -> Inventory:
    for item in station.inventories:
        if item.resource == resource:
            return item
    created = Inventory(resource=resource, amount=Decimal("0"))
    station.inventories.append(created)
    return created


def change_resource(station: Station, resource: str, delta: float) -> float:
    item = ensure_inventory(station, resource)
    current = float(item.amount)
    item.amount = Decimal(f"{current + delta:.2f}")
    return float(item.amount)


def missing_resources(station: Station, cost: dict[str, float]) -> dict[str, float]:
    resources = inventory_map(station)
    result: dict[str, float] = {}
    for resource, amount in cost.items():
        available = resources.get(resource, 0)
        if available < amount:
            result[resource] = round(amount - available, 2)
    return result


def format_missing_resources(cost: dict[str, float], station: Station) -> str:
    missing = missing_resources(station, cost)
    if not missing:
        return ""
    parts = [f"{resource}: {amount:g}" for resource, amount in missing.items()]
    return ", ".join(parts)
