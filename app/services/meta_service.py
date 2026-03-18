from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MetaUpgrade, Station, UserMetaProgress
from app.services.admin_definitions import meta_upgrade_definitions
from app.services.utils import change_resource, inventory_map


def ensure_meta_catalog(db: Session) -> None:
    existing = {upgrade.key: upgrade for upgrade in db.scalars(select(MetaUpgrade)).all()}
    for item in meta_upgrade_definitions(db):
        if not item.get("enabled", True):
            continue
        current = existing.get(str(item["key"]))
        if current:
            current.name = str(item["name"])
            current.description = str(item["description"])
            current.base_cost = int(item["base_cost"])
            current.max_level = int(item["max_level"])
            current.effect_type = str(item["effect_type"])
            current.effect_value = float(item["effect_value"])
        else:
            db.add(
                MetaUpgrade(
                    key=str(item["key"]),
                    name=str(item["name"]),
                    description=str(item["description"]),
                    base_cost=int(item["base_cost"]),
                    max_level=int(item["max_level"]),
                    effect_type=str(item["effect_type"]),
                    effect_value=float(item["effect_value"]),
                )
            )


def list_meta_upgrades(db: Session, user_id: str) -> list[dict[str, object]]:
    ensure_meta_catalog(db)
    upgrades = db.scalars(select(MetaUpgrade).order_by(MetaUpgrade.id)).all()
    progress = {item.upgrade_id: item.level for item in db.scalars(select(UserMetaProgress).where(UserMetaProgress.user_id == user_id)).all()}
    return [
        {
            "key": upgrade.key,
            "name": upgrade.name,
            "description": upgrade.description,
            "base_cost": upgrade.base_cost,
            "max_level": upgrade.max_level,
            "effect_type": upgrade.effect_type,
            "effect_value": upgrade.effect_value,
            "current_level": progress.get(upgrade.id, 0),
        }
        for upgrade in upgrades
    ]


def purchase_meta_upgrade(db: Session, station: Station, key: str) -> None:
    ensure_meta_catalog(db)
    upgrade = db.scalar(select(MetaUpgrade).where(MetaUpgrade.key == key))
    if not upgrade:
        raise HTTPException(status_code=404, detail="Улучшение не найдено.")
    progress = db.scalar(select(UserMetaProgress).where(UserMetaProgress.user_id == station.owner_id, UserMetaProgress.upgrade_id == upgrade.id))
    current_level = progress.level if progress else 0
    if current_level >= upgrade.max_level:
        raise HTTPException(status_code=400, detail="Улучшение уже прокачано до максимума.")
    cost = upgrade.base_cost * (current_level + 1)
    if inventory_map(station).get("insight", 0) < cost:
        raise HTTPException(status_code=400, detail="Недостаточно инсайта.")
    change_resource(station, "insight", -cost)
    if progress:
        progress.level += 1
    else:
        db.add(UserMetaProgress(user_id=station.owner_id, upgrade_id=upgrade.id, level=1))
