from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.game.default_definitions import (
    BASELINE_BALANCE_PARAMETERS,
    BASELINE_CONTRACT_TEMPLATES,
    BASELINE_EVENT_DEFINITIONS,
    BASELINE_META_UPGRADES,
    BASELINE_MODULE_DEFINITIONS,
    BASELINE_RESOURCE_DEFINITIONS,
    BASELINE_SPECIALIZATIONS,
)
from app.models import BalanceParameter, ContentStatus, ContentType, GameContentItem, GameContentRevision
from app.schemas.admin import (
    BalanceUpsertRequest,
    ContractTemplatePayload,
    ContentPayload,
    ContentUpsertRequest,
    EventDefinitionPayload,
    MetaUpgradePayload,
    ModuleDefinitionPayload,
    ResourceDefinitionPayload,
    SpecializationPayload,
    ValidationIssue,
    ValidationResult,
)


_CACHE: dict[str, Any] = {"value": None, "built_at": None}


def invalidate_definitions_cache() -> None:
    _CACHE["value"] = None
    _CACHE["built_at"] = None


def baseline_definitions() -> dict[str, Any]:
    return {
        "resources": deepcopy(BASELINE_RESOURCE_DEFINITIONS),
        "modules": deepcopy(BASELINE_MODULE_DEFINITIONS),
        "events": deepcopy(BASELINE_EVENT_DEFINITIONS),
        "contract_templates": deepcopy(BASELINE_CONTRACT_TEMPLATES),
        "meta_upgrades": deepcopy(BASELINE_META_UPGRADES),
        "specializations": deepcopy(BASELINE_SPECIALIZATIONS),
        "balance": deepcopy(BASELINE_BALANCE_PARAMETERS),
    }


def _content_type_key(content_type: ContentType) -> str:
    return {
        ContentType.resource: "resources",
        ContentType.module: "modules",
        ContentType.event: "events",
        ContentType.contract_template: "contract_templates",
        ContentType.meta_upgrade: "meta_upgrades",
        ContentType.specialization: "specializations",
    }[content_type]


def _payload_schema(content_type: ContentType):
    return {
        ContentType.resource: ResourceDefinitionPayload,
        ContentType.module: ModuleDefinitionPayload,
        ContentType.event: EventDefinitionPayload,
        ContentType.contract_template: ContractTemplatePayload,
        ContentType.meta_upgrade: MetaUpgradePayload,
        ContentType.specialization: SpecializationPayload,
    }[content_type]


def validate_content_payload(
    db: Session, content_type: ContentType, payload: dict[str, object], *, current_key: str | None = None
) -> ValidationResult:
    issues: list[ValidationIssue] = []
    schema = _payload_schema(content_type)
    parsed: ContentPayload | None = None
    try:
        parsed = schema.model_validate(payload)
    except ValidationError as exc:
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"])
            issues.append(ValidationIssue(level="error", field=field, message=str(error["msg"])))
        return ValidationResult(valid=False, issues=issues)

    effective = get_effective_definitions(db, force=True)
    resource_keys = {item["key"] for item in effective["resources"]}
    module_keys = {item["key"] for item in effective["modules"]}

    if isinstance(parsed, ResourceDefinitionPayload):
        if parsed.key == "credits" and not parsed.enabled:
            issues.append(ValidationIssue(level="error", field="enabled", message="Нельзя отключить кредиты."))
    if isinstance(parsed, ModuleDefinitionPayload):
        if any(resource not in resource_keys for resource in parsed.base_cost):
            issues.append(ValidationIssue(level="error", field="base_cost", message="В base_cost есть неизвестный ресурс."))
        if current_key != parsed.key and parsed.key in module_keys:
            issues.append(ValidationIssue(level="warning", field="key", message="Ключ уже есть в baseline и будет переопределён."))
    if isinstance(parsed, ContractTemplatePayload) and parsed.resource not in resource_keys:
        issues.append(ValidationIssue(level="error", field="resource", message="Неизвестный ресурс контракта."))
    if isinstance(parsed, EventDefinitionPayload):
        for resource in parsed.market_effects:
            if resource not in resource_keys:
                issues.append(ValidationIssue(level="error", field="market_effects", message=f"Неизвестный ресурс: {resource}."))
    if isinstance(parsed, SpecializationPayload) and parsed.focus_resource not in resource_keys:
        issues.append(ValidationIssue(level="error", field="focus_resource", message="Неизвестный ресурс специализации."))

    return ValidationResult(valid=not any(item.level == "error" for item in issues), issues=issues)


def validate_balance_payload(request: BalanceUpsertRequest) -> ValidationResult:
    issues: list[ValidationIssue] = []
    if "value" not in request.value:
        issues.append(ValidationIssue(level="error", field="value", message="Ожидается числовое поле value."))
    else:
        try:
            float(request.value["value"])
        except Exception:  # noqa: BLE001
            issues.append(ValidationIssue(level="error", field="value", message="value должен быть числом."))
    return ValidationResult(valid=not issues, issues=issues)


def _merge_content_items(items: list[dict[str, Any]], overrides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {item["key"]: deepcopy(item) for item in items}
    for override in overrides:
        status = override.pop("__status__", "active")
        key = override["key"]
        if status in {ContentStatus.disabled.value, ContentStatus.archived.value}:
            merged.pop(key, None)
            continue
        merged[key] = override
    return sorted(merged.values(), key=lambda item: (item.get("sort_order", 1000), item["key"]))


def get_effective_definitions(db: Session, *, force: bool = False) -> dict[str, Any]:
    if _CACHE["value"] is not None and not force:
        return deepcopy(_CACHE["value"])

    base = baseline_definitions()
    published_items = db.scalars(select(GameContentItem)).all()
    for item in published_items:
        if not item.published_revision_id:
            continue
        revision = db.scalar(
            select(GameContentRevision).where(
                GameContentRevision.content_item_id == item.id,
                GameContentRevision.id == item.published_revision_id,
            )
        )
        if not revision:
            continue
        collection = _content_type_key(item.content_type)
        override_payload = deepcopy(revision.payload_json)
        override_payload["__status__"] = item.status.value
        base[collection] = _merge_content_items(base[collection], [override_payload])

    balance_map = {entry["key"]: deepcopy(entry["value"]) for entry in base["balance"]}
    for parameter in db.scalars(select(BalanceParameter).where(BalanceParameter.enabled.is_(True))).all():
        balance_map[parameter.key] = deepcopy(parameter.value_json)
    base["balance_map"] = balance_map
    base["built_at"] = datetime.now(UTC).isoformat()

    _CACHE["value"] = deepcopy(base)
    _CACHE["built_at"] = datetime.now(UTC)
    return deepcopy(base)


def get_balance_number(db: Session, key: str, default: float) -> float:
    definitions = get_effective_definitions(db)
    value = definitions["balance_map"].get(key)
    if not value:
        return default
    try:
        return float(value["value"])
    except Exception:  # noqa: BLE001
        return default


def resource_definitions_map(db: Session) -> dict[str, dict[str, Any]]:
    return {item["key"]: item for item in get_effective_definitions(db)["resources"]}


def module_definitions_map(db: Session) -> dict[str, dict[str, Any]]:
    return {item["key"]: item for item in get_effective_definitions(db)["modules"]}


def event_definitions(db: Session) -> list[dict[str, Any]]:
    return get_effective_definitions(db)["events"]


def contract_template_definitions(db: Session) -> list[dict[str, Any]]:
    return get_effective_definitions(db)["contract_templates"]


def meta_upgrade_definitions(db: Session) -> list[dict[str, Any]]:
    return get_effective_definitions(db)["meta_upgrades"]


def specialization_definitions_map(db: Session) -> dict[str, dict[str, Any]]:
    return {item["key"]: item for item in get_effective_definitions(db)["specializations"]}
