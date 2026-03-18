from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import DailyReport, Inventory, Notification, NotificationType, PolicyConfig, Station, StationModule
from app.schemas.game import ModuleDefinitionView, ModuleView, ReportView, ResourceAmount, StationView
from app.services.admin_definitions import module_definitions_map, resource_definitions_map
from app.services.utils import change_resource, format_missing_resources, inventory_map


STARTER_MODULE_KEYS = ["dock", "warehouse", "reactor"]


def create_station(db: Session, owner_id: str, sector_id: str, name: str, specialization: str) -> Station:
    station = Station(
        owner_id=owner_id,
        sector_id=sector_id,
        name=name,
        specialization=specialization,
        throughput=14 if specialization == "freight_hub" else 12,
    )
    station.modules = [StationModule(module_key=key, level=1) for key in STARTER_MODULE_KEYS]
    station.inventories = [
        Inventory(resource=key, amount=Decimal(str(definition.get("starting_amount", 0))))
        for key, definition in resource_definitions_map(db).items()
    ]
    station.policies = [
        PolicyConfig(key="market_bias", value="balanced"),
        PolicyConfig(key="contract_focus", value="mixed"),
    ]
    db.add(station)
    db.flush()
    db.add(
        DailyReport(
            station=station,
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            summary={
                "profit": 0,
                "completed_contracts": 0,
                "issues": [],
                "headline": "Станция введена в строй и ждёт первой настройки.",
            },
        )
    )
    db.flush()
    return station


def get_station_for_user(db: Session, user_id: str, *, include_reports: bool = False) -> Station:
    options = [selectinload(Station.modules), selectinload(Station.inventories), selectinload(Station.policies)]
    if include_reports:
        options.append(selectinload(Station.reports))
    station = db.scalar(select(Station).where(Station.owner_id == user_id).options(*options))
    if not station:
        raise ValueError("Station not found")
    return station


def summarize_bottlenecks(station: Station) -> list[str]:
    resources = inventory_map(station)
    issues: list[str] = []
    if resources.get("energy", 0) < 10:
        issues.append("Низкий запас энергии")
    if resources.get("crew", 0) < 3:
        issues.append("Не хватает персонала")
    if resources.get("parts", 0) < 12:
        issues.append("Заканчиваются детали")
    if resources.get("fuel", 0) < 10:
        issues.append("Топливо ограничивает поток")
    if len(station.modules) < 4:
        issues.append("Станции не хватает модульного охвата")
    return issues[:5]


def recommended_actions(station: Station) -> list[str]:
    resources = inventory_map(station)
    actions: list[str] = []
    if resources.get("energy", 0) < 12:
        actions.append("Улучшите реактор или нарастите запас энергии")
    if resources.get("parts", 0) < 18:
        actions.append("Докупите детали на рынке для стабильного ремонта")
    if "market_terminal" not in {module.module_key for module in station.modules}:
        actions.append("Постройте рыночный терминал для лучшей маржи")
    if resources.get("insight", 0) >= 6:
        actions.append("Потратьте инсайт на постоянное улучшение")
    if len(actions) < 4:
        actions.append("Возьмите NPC-контракт для быстрого дохода")
    return actions[:5]


def station_to_view(db: Session, station: Station) -> StationView:
    resources = inventory_map(station)
    module_catalog = [
        definition
        for definition in module_definitions_map(db).values()
        if definition.get("enabled", True) and definition.get("is_visible", True)
    ]
    module_catalog.sort(key=lambda item: (item.get("sort_order", 1000), item["key"]))
    public_resources = [
        definition
        for definition in resource_definitions_map(db).values()
        if definition.get("enabled", True) and definition.get("is_public", True) and definition.get("is_visible", True)
    ]
    public_resources.sort(key=lambda item: (item.get("sort_order", 1000), item["key"]))
    return StationView(
        id=station.id,
        name=station.name,
        level=station.level,
        specialization=station.specialization,
        throughput=station.throughput,
        efficiency=station.efficiency,
        stability=station.stability,
        reputation=station.reputation,
        bottlenecks=summarize_bottlenecks(station),
        recommended_actions=recommended_actions(station),
        inventories=[ResourceAmount(resource=item["key"], amount=resources.get(item["key"], 0)) for item in public_resources],
        modules=[ModuleView(module_key=module.module_key, level=module.level, is_active=module.is_active) for module in station.modules],
        module_catalog=[
            ModuleDefinitionView(
                key=item["key"],
                name=str(item.get("name", item["key"])),
                description=str(item.get("description", "")),
                category=str(item.get("category", "module")),
                max_level=int(item.get("max_level", 1)),
                base_cost={resource: float(amount) for resource, amount in dict(item.get("base_cost", {})).items()},
                upgrade_cost_growth=float(item.get("upgrade_cost_growth", 0.45)),
                energy_delta=float(item.get("energy_delta", 0)),
                throughput_delta=float(item.get("throughput_delta", 0)),
                crew_requirement=int(item.get("crew_requirement", 0)),
                sort_order=int(item.get("sort_order", 1000)),
            )
            for item in module_catalog
        ],
        last_processed_at=station.last_processed_at,
    )


def rename_station(station: Station, name: str) -> None:
    station.name = name


def apply_policy(station: Station, key: str, value: str) -> None:
    for policy in station.policies:
        if policy.key == key:
            policy.value = value
            return
    station.policies.append(PolicyConfig(key=key, value=value))


def module_upgrade_cost(module_definition: dict[str, object], level: int) -> dict[str, float]:
    base_cost = {resource: float(amount) for resource, amount in dict(module_definition.get("base_cost", {})).items()}
    multiplier = 1 + (level - 1) * float(module_definition.get("upgrade_cost_growth", 0.45))
    return {resource: round(amount * multiplier, 2) for resource, amount in base_cost.items()}


def can_afford(station: Station, cost: dict[str, float]) -> bool:
    resources = inventory_map(station)
    return all(resources.get(resource, 0) >= amount for resource, amount in cost.items())


def pay_cost(station: Station, cost: dict[str, float]) -> None:
    for resource, amount in cost.items():
        change_resource(station, resource, -amount)


def build_or_upgrade_module(db: Session, station: Station, module_key: str) -> StationModule:
    modules = module_definitions_map(db)
    module_definition = modules.get(module_key)
    if not module_definition or not module_definition.get("enabled", True):
        raise ValueError("Unknown module")

    existing = next((module for module in station.modules if module.module_key == module_key), None)
    target_level = existing.level + 1 if existing else 1
    if target_level > int(module_definition.get("max_level", 10)):
        raise ValueError("Module reached max level")
    cost = module_upgrade_cost(module_definition, target_level)
    if not can_afford(station, cost):
        missing = format_missing_resources(cost, station)
        raise ValueError(f"Недостаточно ресурсов: {missing}")

    pay_cost(station, cost)
    if existing:
        existing.level += 1
        result = existing
    else:
        result = StationModule(module_key=module_key, level=1)
        station.modules.append(result)

    db.add(
        Notification(
            user_id=station.owner_id,
            type=NotificationType.system,
            title="Модуль обновлён",
            message=f"{module_definition.get('name', module_key)}: теперь уровень {result.level}.",
            payload={"module_key": module_key, "level": result.level},
        )
    )
    return result


def list_reports(db: Session, station_id: str, limit: int = 10) -> list[ReportView]:
    ordered = db.scalars(
        select(DailyReport).where(DailyReport.station_id == station_id).order_by(DailyReport.ended_at.desc()).limit(limit)
    ).all()
    return [ReportView.model_validate(report) for report in ordered]
