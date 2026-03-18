from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    AdminAuditLog,
    AdminRoleKey,
    BalanceParameter,
    BalanceRevision,
    Contract,
    ContentSourceKind,
    ContentStatus,
    ContentType,
    DailyReport,
    GameContentItem,
    GameContentRevision,
    Inventory,
    MarketState,
    MarketTransaction,
    Notification,
    PlayerTransfer,
    PolicyConfig,
    Role,
    ResearchQueue,
    Station,
    StationModule,
    User,
    UserMetaProgress,
    UserRole,
    WorldEvent,
)
from app.schemas.admin import (
    AdminPlayerDetailView,
    AdminPlayerSummaryView,
    AdminPlayerUpdateRequest,
    AdminUserView,
    BalanceItemView,
    BalanceRevisionView,
    BalanceUpsertRequest,
    ContentDiffView,
    ContentItemView,
    ContentRevisionView,
    ContentUpsertRequest,
    RoleAssignmentRequest,
)
from app.services.admin_definitions import (
    baseline_definitions,
    invalidate_definitions_cache,
    module_definitions_map,
    resource_definitions_map,
    specialization_definitions_map,
    validate_balance_payload,
    validate_content_payload,
)
from app.services.utils import inventory_map


STARTER_MODULE_KEYS = ["dock", "warehouse", "reactor"]


ROLE_PERMISSIONS: dict[AdminRoleKey, set[str]] = {
    AdminRoleKey.super_admin: {"*"},
    AdminRoleKey.admin: {
        "admin.read",
        "players.read",
        "players.edit",
        "players.wipe",
        "server.wipe",
        "content.edit",
        "content.publish",
        "balance.edit",
        "balance.publish",
        "audit.read",
        "roles.read",
    },
    AdminRoleKey.designer: {
        "admin.read",
        "players.read",
        "content.edit",
        "content.publish",
        "balance.edit",
        "balance.publish",
    },
    AdminRoleKey.moderator: {"admin.read", "audit.read", "players.read"},
}


def ensure_roles_seeded(db: Session) -> None:
    existing = {role.key for role in db.scalars(select(Role)).all()}
    for key in AdminRoleKey:
        if key in existing:
            continue
        db.add(Role(key=key, name=key.value.replace("_", " ").title(), description=f"Role {key.value}"))
    db.flush()


def ensure_system_content_seeded(db: Session) -> None:
    baseline = baseline_definitions()
    for content_type, collection_key in [
        (ContentType.resource, "resources"),
        (ContentType.module, "modules"),
        (ContentType.event, "events"),
        (ContentType.contract_template, "contract_templates"),
        (ContentType.meta_upgrade, "meta_upgrades"),
        (ContentType.specialization, "specializations"),
    ]:
        for payload in baseline[collection_key]:
            item = db.scalar(select(GameContentItem).where(GameContentItem.content_type == content_type, GameContentItem.key == payload["key"]))
            if item:
                continue
            item = GameContentItem(
                content_type=content_type,
                key=str(payload["key"]),
                display_name=str(payload.get("name") or payload.get("title") or payload["key"]),
                source_kind=ContentSourceKind.system,
                status=ContentStatus.active,
                tags=list(payload.get("tags", [])),
            )
            db.add(item)
            db.flush()
            revision = GameContentRevision(
                content_item_id=item.id,
                version=1,
                payload_json=payload,
                change_summary="Baseline import",
                is_published=True,
                published_at=datetime.now(UTC),
            )
            db.add(revision)
            db.flush()
            item.current_revision_id = revision.id
            item.published_revision_id = revision.id
    for parameter in baseline["balance"]:
        item = db.scalar(select(BalanceParameter).where(BalanceParameter.key == parameter["key"]))
        if item:
            continue
        item = BalanceParameter(
            key=str(parameter["key"]),
            category=str(parameter["category"]),
            scope=str(parameter["scope"]),
            enabled=True,
            value_json=dict(parameter["value"]),
        )
        db.add(item)
        db.flush()
        revision = BalanceRevision(
            balance_parameter_id=item.id,
            version=1,
            value_json=dict(parameter["value"]),
            change_summary="Baseline import",
            is_published=True,
            published_at=datetime.now(UTC),
        )
        db.add(revision)
        db.flush()
        item.current_revision_id = revision.id
        item.published_revision_id = revision.id


def get_user_role_names(db: Session, user_id: str) -> list[AdminRoleKey]:
    ensure_roles_seeded(db)
    rows = db.scalars(select(UserRole).where(UserRole.user_id == user_id)).all()
    return [row.role.key for row in rows if row.role]


def effective_permissions(role_names: list[AdminRoleKey]) -> list[str]:
    permissions: set[str] = set()
    for role in role_names:
        permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return sorted(permissions)


def ensure_permission(db: Session, user: User, permission: str) -> list[AdminRoleKey]:
    roles = get_user_role_names(db, user.id)
    perms = effective_permissions(roles)
    if "*" in perms or permission in perms:
        return roles
    raise HTTPException(status_code=403, detail="Недостаточно прав.")


def audit(db: Session, actor: User | None, action_type: str, target_type: str, target_id: str, summary: str, metadata: dict[str, object] | None = None) -> None:
    db.add(
        AdminAuditLog(
            actor_user_id=actor.id if actor else None,
            action_type=action_type,
            target_type=target_type,
            target_id=str(target_id),
            summary=summary,
            metadata_json=metadata or {},
        )
    )


def list_admin_users(db: Session) -> list[AdminUserView]:
    ensure_roles_seeded(db)
    users = db.scalars(select(User).order_by(User.username.asc())).all()
    return [
        AdminUserView(
            id=user.id,
            username=user.username,
            email=user.email,
            roles=get_user_role_names(db, user.id),
        )
        for user in users
    ]


def _player_summary_view(station: Station) -> AdminPlayerSummaryView:
    user = station.owner
    return AdminPlayerSummaryView(
        station_id=station.id,
        owner_user_id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        station_name=station.name,
        specialization=station.specialization,
        level=station.level,
        throughput=station.throughput,
        efficiency=station.efficiency,
        stability=station.stability,
        reputation=station.reputation,
        updated_at=station.updated_at,
    )


def list_admin_players(db: Session) -> list[AdminPlayerSummaryView]:
    stations = db.scalars(
        select(Station)
        .options(selectinload(Station.owner))
        .order_by(Station.updated_at.desc())
    ).all()
    return [_player_summary_view(station) for station in stations if station.owner]


def get_admin_player_detail(db: Session, station_id: str) -> AdminPlayerDetailView:
    station = db.scalar(
        select(Station)
        .where(Station.id == station_id)
        .options(selectinload(Station.owner), selectinload(Station.inventories), selectinload(Station.modules))
    )
    if not station or not station.owner:
        raise HTTPException(status_code=404, detail="Игрок или станция не найдены.")
    summary = _player_summary_view(station)
    inventories = [
        {"resource": item.resource, "amount": float(item.amount)}
        for item in sorted(station.inventories, key=lambda item: item.resource)
    ]
    modules = [
        {"module_key": item.module_key, "level": item.level, "is_active": item.is_active}
        for item in sorted(station.modules, key=lambda item: item.module_key)
    ]
    return AdminPlayerDetailView(
        **summary.model_dump(),
        public_notes=station.public_notes,
        inventories=inventories,
        modules=modules,
        last_processed_at=station.last_processed_at,
    )


def update_admin_player(db: Session, actor: User, station_id: str, payload: AdminPlayerUpdateRequest) -> AdminPlayerDetailView:
    ensure_permission(db, actor, "players.edit")
    station = db.scalar(
        select(Station)
        .where(Station.id == station_id)
        .options(selectinload(Station.owner), selectinload(Station.inventories), selectinload(Station.modules))
    )
    if not station or not station.owner:
        raise HTTPException(status_code=404, detail="Игрок или станция не найдены.")

    specialization_map = specialization_definitions_map(db)
    resource_map = resource_definitions_map(db)
    module_map = module_definitions_map(db)

    if payload.specialization is not None and payload.specialization not in specialization_map:
        raise HTTPException(status_code=400, detail="Неизвестная специализация.")

    if payload.station_name is not None:
        station.name = payload.station_name
    if payload.specialization is not None:
        station.specialization = payload.specialization
    if payload.level is not None:
        station.level = payload.level
    if payload.throughput is not None:
        station.throughput = payload.throughput
    if payload.efficiency is not None:
        station.efficiency = payload.efficiency
    if payload.stability is not None:
        station.stability = payload.stability
    if payload.reputation is not None:
        station.reputation = payload.reputation
    if payload.public_notes is not None:
        station.public_notes = payload.public_notes
    if payload.is_active is not None:
        station.owner.is_active = payload.is_active

    inventory_by_resource = {item.resource: item for item in station.inventories}
    for item in payload.inventories:
        if item.resource not in resource_map:
            raise HTTPException(status_code=400, detail=f"Неизвестный ресурс: {item.resource}")
        row = inventory_by_resource.get(item.resource)
        if row is None:
            row = Inventory(station_id=station.id, resource=item.resource, amount=item.amount)
            station.inventories.append(row)
            inventory_by_resource[item.resource] = row
        else:
            row.amount = item.amount

    modules_by_key = {item.module_key: item for item in station.modules}
    for item in payload.modules:
        if item.module_key not in module_map:
            raise HTTPException(status_code=400, detail=f"Неизвестный модуль: {item.module_key}")
        row = modules_by_key.get(item.module_key)
        if row is None:
            row = StationModule(station_id=station.id, module_key=item.module_key, level=item.level, is_active=item.is_active)
            station.modules.append(row)
            modules_by_key[item.module_key] = row
        else:
            row.level = item.level
            row.is_active = item.is_active

    audit(
        db,
        actor,
        "player.update",
        "station",
        station.id,
        f"Обновлены показатели игрока {station.owner.username}",
        {
            "level": payload.level,
            "specialization": payload.specialization,
            "resource_edits": [item.resource for item in payload.inventories],
            "module_edits": [item.module_key for item in payload.modules],
        },
    )
    return get_admin_player_detail(db, station.id)


def _reset_station_state(db: Session, station: Station) -> None:
    resource_map = resource_definitions_map(db)
    db.query(StationModule).filter(StationModule.station_id == station.id).delete()
    db.query(Inventory).filter(Inventory.station_id == station.id).delete()
    db.query(DailyReport).filter(DailyReport.station_id == station.id).delete()
    db.query(PolicyConfig).filter(PolicyConfig.station_id == station.id).delete()
    db.query(ResearchQueue).filter(ResearchQueue.station_id == station.id).delete()
    db.query(Contract).filter(
        (Contract.issuer_station_id == station.id) | (Contract.taker_station_id == station.id)
    ).delete()
    db.query(PlayerTransfer).filter(
        (PlayerTransfer.from_station_id == station.id) | (PlayerTransfer.to_station_id == station.id)
    ).delete()
    db.query(MarketTransaction).filter(MarketTransaction.station_id == station.id).delete()
    db.query(Notification).filter(Notification.user_id == station.owner_id).delete()
    db.query(UserMetaProgress).filter(UserMetaProgress.user_id == station.owner_id).delete()

    station.level = 1
    station.specialization = "freight_hub"
    station.throughput = 14.0
    station.efficiency = 1.0
    station.stability = 100.0
    station.reputation = 0.0
    station.policy_config = {}
    station.public_notes = ""
    station.last_processed_at = datetime.now(UTC)
    station.last_report_claimed_at = None

    station.modules = [StationModule(module_key=key, level=1, is_active=True) for key in STARTER_MODULE_KEYS]
    station.inventories = [
        Inventory(resource=key, amount=Decimal(str(definition.get("starting_amount", 0))))
        for key, definition in resource_map.items()
    ]
    station.policies = [
        PolicyConfig(key="market_bias", value="balanced"),
        PolicyConfig(key="contract_focus", value="mixed"),
    ]
    db.add(
        DailyReport(
            station=station,
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
            summary={
                "profit": 0,
                "completed_contracts": 0,
                "issues": [],
                "headline": "Станция прошла полный сброс и готова к новому циклу.",
            },
        )
    )


def wipe_player_progress(db: Session, actor: User, station_id: str) -> AdminPlayerDetailView:
    ensure_permission(db, actor, "players.wipe")
    station = db.scalar(
        select(Station)
        .where(Station.id == station_id)
        .options(selectinload(Station.owner), selectinload(Station.inventories), selectinload(Station.modules))
    )
    if not station or not station.owner:
        raise HTTPException(status_code=404, detail="Игрок или станция не найдены.")
    _reset_station_state(db, station)
    audit(db, actor, "player.wipe", "station", station.id, f"Сброшен прогресс игрока {station.owner.username}")
    return get_admin_player_detail(db, station.id)


def wipe_server_progress(db: Session, actor: User) -> dict[str, int]:
    ensure_permission(db, actor, "server.wipe")
    stations = db.scalars(
        select(Station).options(selectinload(Station.owner), selectinload(Station.inventories), selectinload(Station.modules))
    ).all()
    sectors = db.scalars(select(MarketState)).all()

    db.query(WorldEvent).delete()
    db.query(Contract).delete()
    db.query(PlayerTransfer).delete()
    db.query(MarketTransaction).delete()
    db.query(Notification).delete()
    db.query(UserMetaProgress).delete()
    db.query(DailyReport).delete()
    db.query(PolicyConfig).delete()
    db.query(ResearchQueue).delete()
    db.query(StationModule).delete()
    db.query(Inventory).delete()

    for station in stations:
        station.level = 1
        station.specialization = "freight_hub"
        station.throughput = 14.0
        station.efficiency = 1.0
        station.stability = 100.0
        station.reputation = 0.0
        station.policy_config = {}
        station.public_notes = ""
        station.last_processed_at = datetime.now(UTC)
        station.last_report_claimed_at = None
        station.modules = [StationModule(module_key=key, level=1, is_active=True) for key in STARTER_MODULE_KEYS]
        station.inventories = [
            Inventory(resource=key, amount=Decimal(str(definition.get("starting_amount", 0))))
            for key, definition in resource_definitions_map(db).items()
        ]
        station.policies = [
            PolicyConfig(key="market_bias", value="balanced"),
            PolicyConfig(key="contract_focus", value="mixed"),
        ]
        db.add(
            DailyReport(
                station=station,
                started_at=datetime.now(UTC),
                ended_at=datetime.now(UTC),
                summary={
                    "profit": 0,
                    "completed_contracts": 0,
                    "issues": [],
                    "headline": "Станция синхронизирована после серверного вайпа.",
                },
            )
        )

    resource_map = resource_definitions_map(db)
    for market in sectors:
        definition = resource_map.get(market.resource)
        if not definition:
            continue
        base_price = float(definition.get("base_price", 10))
        market.price = base_price
        market.trend = 0.0
        market.history = [base_price]

    audit(db, actor, "server.wipe", "server", "all", "Выполнен полный серверный вайп игрового прогресса", {"stations": len(stations)})
    return {"stations_reset": len(stations)}


def assign_roles(db: Session, actor: User, payload: RoleAssignmentRequest) -> None:
    ensure_permission(db, actor, "*")
    ensure_roles_seeded(db)
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")
    db.query(UserRole).filter(UserRole.user_id == user.id).delete()
    roles = {role.key: role for role in db.scalars(select(Role)).all()}
    for role_key in payload.roles:
        db.add(UserRole(user_id=user.id, role_id=roles[role_key].id))
    audit(db, actor, "roles.assign", "user", user.id, f"Обновлены роли {user.username}", {"roles": [role.value for role in payload.roles]})


def _item_to_view(item: GameContentItem, revision: GameContentRevision | None = None) -> ContentItemView:
    return ContentItemView(
        id=item.id,
        content_type=item.content_type,
        key=item.key,
        display_name=item.display_name,
        source_kind=item.source_kind,
        status=item.status,
        tags=item.tags,
        current_revision_id=item.current_revision_id,
        published_revision_id=item.published_revision_id,
        updated_by=item.updated_by,
        updated_at=item.updated_at,
        payload=deepcopy(revision.payload_json) if revision else None,
    )


def list_content_items(db: Session, content_type: ContentType | None = None, status: ContentStatus | None = None, search: str | None = None) -> list[ContentItemView]:
    query = select(GameContentItem).order_by(GameContentItem.updated_at.desc())
    if content_type:
        query = query.where(GameContentItem.content_type == content_type)
    if status:
        query = query.where(GameContentItem.status == status)
    items = db.scalars(query).all()
    if search:
        needle = search.lower()
        items = [item for item in items if needle in item.key.lower() or needle in item.display_name.lower()]
    result: list[ContentItemView] = []
    for item in items:
        revision = None
        if item.current_revision_id:
            revision = db.scalar(select(GameContentRevision).where(GameContentRevision.id == item.current_revision_id))
        result.append(_item_to_view(item, revision))
    return result


def get_content_item(db: Session, content_type: ContentType, key: str) -> ContentItemView:
    item = db.scalar(select(GameContentItem).where(GameContentItem.content_type == content_type, GameContentItem.key == key))
    if not item:
        raise HTTPException(status_code=404, detail="Контент не найден.")
    revision = db.scalar(select(GameContentRevision).where(GameContentRevision.id == item.current_revision_id)) if item.current_revision_id else None
    return _item_to_view(item, revision)


def upsert_content_draft(db: Session, actor: User, payload: ContentUpsertRequest) -> ContentItemView:
    ensure_permission(db, actor, "content.edit")
    validation = validate_content_payload(db, payload.content_type, payload.payload, current_key=payload.key)
    blocking = [issue for issue in validation.issues if issue.level == "error"]
    if blocking:
        raise HTTPException(status_code=400, detail=[issue.model_dump() for issue in blocking])

    item = db.scalar(select(GameContentItem).where(GameContentItem.content_type == payload.content_type, GameContentItem.key == payload.key))
    if not item:
        item = GameContentItem(
            content_type=payload.content_type,
            key=payload.key,
            display_name=payload.display_name,
            source_kind=ContentSourceKind.admin,
            status=ContentStatus.draft,
            tags=payload.tags,
            created_by=actor.id,
            updated_by=actor.id,
        )
        db.add(item)
        db.flush()
    else:
        item.display_name = payload.display_name
        item.tags = payload.tags
        item.updated_by = actor.id

    version = len(item.revisions) + 1
    revision = GameContentRevision(
        content_item_id=item.id,
        version=version,
        payload_json=payload.payload,
        change_summary=payload.summary,
        author_user_id=actor.id,
        is_published=False,
    )
    db.add(revision)
    db.flush()
    item.current_revision_id = revision.id
    audit(db, actor, "content.save_draft", payload.content_type.value, payload.key, f"Сохранён draft {payload.key}", {"version": version})
    return _item_to_view(item, revision)


def publish_content(db: Session, actor: User, content_type: ContentType, key: str) -> ContentItemView:
    ensure_permission(db, actor, "content.publish")
    item = db.scalar(select(GameContentItem).where(GameContentItem.content_type == content_type, GameContentItem.key == key))
    if not item or not item.current_revision_id:
        raise HTTPException(status_code=404, detail="Контент не найден.")
    revision = db.scalar(select(GameContentRevision).where(GameContentRevision.id == item.current_revision_id))
    if not revision:
        raise HTTPException(status_code=404, detail="Ревизия не найдена.")
    revision.is_published = True
    revision.published_at = datetime.now(UTC)
    item.published_revision_id = revision.id
    item.status = ContentStatus.active
    item.updated_by = actor.id
    invalidate_definitions_cache()
    audit(db, actor, "content.publish", content_type.value, key, f"Опубликован {key}", {"revision_id": revision.id})
    return _item_to_view(item, revision)


def change_content_status(db: Session, actor: User, content_type: ContentType, key: str, status: ContentStatus) -> ContentItemView:
    ensure_permission(db, actor, "content.publish")
    item = db.scalar(select(GameContentItem).where(GameContentItem.content_type == content_type, GameContentItem.key == key))
    if not item:
        raise HTTPException(status_code=404, detail="Контент не найден.")
    item.status = status
    item.updated_by = actor.id
    invalidate_definitions_cache()
    audit(db, actor, f"content.{status.value}", content_type.value, key, f"{key}: статус {status.value}")
    revision = db.scalar(select(GameContentRevision).where(GameContentRevision.id == item.current_revision_id)) if item.current_revision_id else None
    return _item_to_view(item, revision)


def duplicate_content(db: Session, actor: User, content_type: ContentType, key: str, new_key: str) -> ContentItemView:
    source = db.scalar(select(GameContentItem).where(GameContentItem.content_type == content_type, GameContentItem.key == key))
    if not source or not source.current_revision_id:
        raise HTTPException(status_code=404, detail="Источник не найден.")
    revision = db.scalar(select(GameContentRevision).where(GameContentRevision.id == source.current_revision_id))
    if not revision:
        raise HTTPException(status_code=404, detail="Ревизия источника не найдена.")
    payload = deepcopy(revision.payload_json)
    payload["key"] = new_key
    return upsert_content_draft(
        db,
        actor,
        ContentUpsertRequest(
            content_type=content_type,
            key=new_key,
            display_name=f"{source.display_name} Copy",
            summary=f"Duplicate of {key}",
            payload=payload,
            tags=source.tags,
        ),
    )


def list_content_revisions(db: Session, content_type: ContentType, key: str) -> list[ContentRevisionView]:
    item = db.scalar(select(GameContentItem).where(GameContentItem.content_type == content_type, GameContentItem.key == key))
    if not item:
        raise HTTPException(status_code=404, detail="Контент не найден.")
    return [ContentRevisionView.model_validate(revision) for revision in item.revisions]


def content_diff(db: Session, content_type: ContentType, key: str, from_version: int, to_version: int) -> ContentDiffView:
    item = db.scalar(select(GameContentItem).where(GameContentItem.content_type == content_type, GameContentItem.key == key))
    if not item:
        raise HTTPException(status_code=404, detail="Контент не найден.")
    revisions = {revision.version: revision for revision in item.revisions}
    if from_version not in revisions or to_version not in revisions:
        raise HTTPException(status_code=404, detail="Версия не найдена.")
    return ContentDiffView(
        from_version=from_version,
        to_version=to_version,
        before=revisions[from_version].payload_json,
        after=revisions[to_version].payload_json,
    )


def rollback_content(db: Session, actor: User, content_type: ContentType, key: str, version: int) -> ContentItemView:
    item = db.scalar(select(GameContentItem).where(GameContentItem.content_type == content_type, GameContentItem.key == key))
    if not item:
        raise HTTPException(status_code=404, detail="Контент не найден.")
    target = next((revision for revision in item.revisions if revision.version == version), None)
    if not target:
        raise HTTPException(status_code=404, detail="Ревизия не найдена.")
    draft = upsert_content_draft(
        db,
        actor,
        ContentUpsertRequest(
            content_type=content_type,
            key=key,
            display_name=item.display_name,
            summary=f"Rollback to version {version}",
            payload=target.payload_json,
            tags=item.tags,
        ),
    )
    publish_content(db, actor, content_type, key)
    audit(db, actor, "content.rollback", content_type.value, key, f"Откат {key} к версии {version}")
    return draft


def list_balance(db: Session) -> list[BalanceItemView]:
    return [BalanceItemView.model_validate(item) for item in db.scalars(select(BalanceParameter).order_by(BalanceParameter.category, BalanceParameter.key)).all()]


def upsert_balance(db: Session, actor: User, payload: BalanceUpsertRequest) -> BalanceItemView:
    ensure_permission(db, actor, "balance.edit")
    validation = validate_balance_payload(payload)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=[issue.model_dump() for issue in validation.issues])
    item = db.scalar(select(BalanceParameter).where(BalanceParameter.key == payload.key))
    if not item:
        item = BalanceParameter(
            key=payload.key,
            category=payload.category,
            scope=payload.scope,
            enabled=payload.enabled,
            value_json=payload.value,
            created_by=actor.id,
            updated_by=actor.id,
        )
        db.add(item)
        db.flush()
    else:
        item.category = payload.category
        item.scope = payload.scope
        item.enabled = payload.enabled
        item.value_json = payload.value
        item.updated_by = actor.id
    revision = BalanceRevision(
        balance_parameter_id=item.id,
        version=len(item.revisions) + 1,
        value_json=payload.value,
        change_summary=payload.summary,
        author_user_id=actor.id,
        is_published=False,
    )
    db.add(revision)
    db.flush()
    item.current_revision_id = revision.id
    audit(db, actor, "balance.save_draft", "balance", payload.key, f"Сохранён баланс {payload.key}", {"version": revision.version})
    return BalanceItemView.model_validate(item)


def publish_balance(db: Session, actor: User, key: str) -> BalanceItemView:
    ensure_permission(db, actor, "balance.publish")
    item = db.scalar(select(BalanceParameter).where(BalanceParameter.key == key))
    if not item or not item.current_revision_id:
        raise HTTPException(status_code=404, detail="Параметр не найден.")
    revision = db.scalar(select(BalanceRevision).where(BalanceRevision.id == item.current_revision_id))
    if not revision:
        raise HTTPException(status_code=404, detail="Ревизия не найдена.")
    revision.is_published = True
    revision.published_at = datetime.now(UTC)
    item.published_revision_id = revision.id
    invalidate_definitions_cache()
    audit(db, actor, "balance.publish", "balance", key, f"Опубликован баланс {key}", {"revision_id": revision.id})
    return BalanceItemView.model_validate(item)


def list_balance_revisions(db: Session, key: str) -> list[BalanceRevisionView]:
    item = db.scalar(select(BalanceParameter).where(BalanceParameter.key == key))
    if not item:
        raise HTTPException(status_code=404, detail="Параметр не найден.")
    return [BalanceRevisionView.model_validate(revision) for revision in item.revisions]


def rollback_balance(db: Session, actor: User, key: str, version: int) -> BalanceItemView:
    item = db.scalar(select(BalanceParameter).where(BalanceParameter.key == key))
    if not item:
        raise HTTPException(status_code=404, detail="Параметр не найден.")
    target = next((revision for revision in item.revisions if revision.version == version), None)
    if not target:
        raise HTTPException(status_code=404, detail="Ревизия не найдена.")
    upsert_balance(
        db,
        actor,
        BalanceUpsertRequest(
            key=key,
            category=item.category,
            scope=item.scope,
            summary=f"Rollback to version {version}",
            value=target.value_json,
            enabled=item.enabled,
        ),
    )
    result = publish_balance(db, actor, key)
    audit(db, actor, "balance.rollback", "balance", key, f"Откат баланса {key} к версии {version}")
    return result


def list_audit_logs(db: Session, limit: int = 100) -> list[AdminAuditLog]:
    return db.scalars(select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(limit)).all()
