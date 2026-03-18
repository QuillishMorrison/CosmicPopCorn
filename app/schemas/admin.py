from __future__ import annotations

from datetime import datetime
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models import AdminRoleKey, ContentSourceKind, ContentStatus, ContentType
from app.schemas.common import BaseSchema


class EffectDefinition(BaseModel):
    type: Literal[
        "add_resource_production",
        "multiply_resource_production",
        "add_storage_capacity",
        "add_energy_generation",
        "add_energy_consumption",
        "add_market_bonus",
        "add_contract_reward_bonus",
        "add_reputation_gain",
        "add_station_stat",
        "apply_sector_modifier",
        "apply_event_weight_modifier",
    ]
    resource: str | None = None
    stat: str | None = None
    target: str | None = None
    value: float | None = None
    multiplier: float | None = None

    @model_validator(mode="after")
    def validate_fields(self) -> "EffectDefinition":
        if self.type in {"add_resource_production", "multiply_resource_production"} and not self.resource:
            raise ValueError("Для эффекта ресурса нужен ключ resource.")
        if self.type == "add_station_stat" and not self.stat:
            raise ValueError("Для station stat нужен ключ stat.")
        if self.type in {"apply_sector_modifier", "apply_event_weight_modifier"} and not self.target:
            raise ValueError("Для модификатора нужен target.")
        if self.type == "multiply_resource_production":
            if self.multiplier is None or self.multiplier <= 0:
                raise ValueError("Multiplier должен быть больше 0.")
        elif self.value is None:
            raise ValueError("Value обязателен для этого эффекта.")
        return self


class ConditionRule(BaseModel):
    field: Literal[
        "sector_player_count",
        "market.energy_price",
        "market.fuel_price",
        "market.parts_price",
        "market.data_price",
        "market.alloy_price",
        "station_specialization",
        "world_state_tag",
    ]
    op: Literal["==", "!=", ">", ">=", "<", "<=", "contains"]
    value: str | float | int


class ConditionGroup(BaseModel):
    all: list[ConditionRule] = Field(default_factory=list)
    any: list[ConditionRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_non_empty(self) -> "ConditionGroup":
        if not self.all and not self.any:
            raise ValueError("Нужно хотя бы одно условие.")
        return self


SLUG_PATTERN = re.compile(r"^[a-z0-9_]+$")


def _validate_slug(value: str) -> str:
    if not SLUG_PATTERN.fullmatch(value):
        raise ValueError(
            "Поле key — это технический slug. Используйте только латиницу в нижнем регистре, цифры и _. Например: biofuel_cell"
        )
    return value


class ResourceDefinitionPayload(BaseModel):
    key: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=4, max_length=300)
    icon_key: str = Field(min_length=2, max_length=40)
    rarity: str = Field(min_length=2, max_length=30)
    category: str = Field(min_length=2, max_length=40)
    base_price: float = Field(ge=0)
    sort_order: int = Field(default=100, ge=0, le=10000)
    is_public: bool = True
    is_visible: bool = True
    enabled: bool = True
    starting_amount: float = Field(default=0, ge=0, le=1000000)

    _key_validator = field_validator("key")(_validate_slug)


class ModuleDefinitionPayload(BaseModel):
    key: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=4, max_length=400)
    category: str = Field(min_length=2, max_length=40)
    max_level: int = Field(ge=1, le=100)
    base_cost: dict[str, float]
    upgrade_cost_growth: float = Field(ge=0, le=10)
    base_effect: dict[str, float] = Field(default_factory=dict)
    effects: list[EffectDefinition] = Field(default_factory=list)
    energy_delta: float = Field(ge=-1000, le=1000)
    throughput_delta: float = Field(ge=-1000, le=1000)
    crew_delta: float = Field(default=0, ge=-1000, le=1000)
    crew_requirement: int = Field(default=0, ge=0, le=1000)
    unlock_requirements: list[str] = Field(default_factory=list)
    specialization_tags: list[str] = Field(default_factory=list)
    sort_order: int = Field(default=100, ge=0, le=10000)
    enabled: bool = True
    is_visible: bool = True

    _key_validator = field_validator("key")(_validate_slug)

    @model_validator(mode="after")
    def validate_cost(self) -> "ModuleDefinitionPayload":
        if not self.base_cost:
            raise ValueError("Нужна хотя бы одна стоимость.")
        if any(value <= 0 for value in self.base_cost.values()):
            raise ValueError("Все значения base_cost должны быть больше 0.")
        return self


class EventDefinitionPayload(BaseModel):
    key: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=2, max_length=120)
    short_description: str = Field(min_length=4, max_length=200)
    long_description: str = Field(min_length=8, max_length=600)
    event_type: str = Field(min_length=2, max_length=40)
    duration_minutes: int = Field(ge=5, le=24 * 60)
    weight: float = Field(gt=0, le=100)
    conditions: ConditionGroup
    market_effects: dict[str, float] = Field(default_factory=dict)
    effects: list[EffectDefinition] = Field(default_factory=list)
    scope: Literal["sector", "global"] = "sector"
    enabled: bool = True
    cooldown_minutes: int = Field(default=30, ge=0, le=24 * 60)
    tags: list[str] = Field(default_factory=list)

    _key_validator = field_validator("key")(_validate_slug)


class ContractTemplatePayload(BaseModel):
    key: str = Field(min_length=2, max_length=40)
    title: str = Field(min_length=2, max_length=120)
    contract_type: str = Field(min_length=2, max_length=40)
    resource: str = Field(min_length=2, max_length=40)
    quantity: float = Field(gt=0, le=100000)
    reward_credits: float = Field(gt=0, le=1000000)
    reward_reputation: float = Field(default=0, ge=0, le=1000)
    enabled: bool = True
    tags: list[str] = Field(default_factory=list)

    _key_validator = field_validator("key")(_validate_slug)


class MetaUpgradePayload(BaseModel):
    key: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=4, max_length=255)
    base_cost: int = Field(gt=0, le=100000)
    max_level: int = Field(ge=1, le=50)
    effect_type: str = Field(min_length=2, max_length=60)
    effect_value: float = Field(ge=0, le=1000)
    enabled: bool = True

    _key_validator = field_validator("key")(_validate_slug)


class SpecializationPayload(BaseModel):
    key: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=4, max_length=255)
    throughput_multiplier: float = Field(ge=0.1, le=10)
    focus_resource: str = Field(min_length=2, max_length=40)
    sort_order: int = Field(default=100, ge=0, le=10000)
    enabled: bool = True

    _key_validator = field_validator("key")(_validate_slug)


ContentPayload = (
    ResourceDefinitionPayload
    | ModuleDefinitionPayload
    | EventDefinitionPayload
    | ContractTemplatePayload
    | MetaUpgradePayload
    | SpecializationPayload
)


class ContentUpsertRequest(BaseModel):
    content_type: ContentType
    key: str = Field(min_length=2, max_length=80)
    display_name: str = Field(min_length=2, max_length=120)
    summary: str = Field(default="", max_length=255)
    payload: dict[str, object]
    tags: list[str] = Field(default_factory=list)

    _key_validator = field_validator("key")(_validate_slug)


class BalanceUpsertRequest(BaseModel):
    key: str = Field(min_length=2, max_length=80)
    category: str = Field(min_length=2, max_length=80)
    scope: str = Field(default="global", min_length=2, max_length=40)
    summary: str = Field(default="", max_length=255)
    value: dict[str, object]
    enabled: bool = True


class ContentRevisionView(BaseSchema):
    id: int
    version: int
    change_summary: str
    is_published: bool
    published_at: datetime | None
    author_user_id: str | None
    payload_json: dict[str, object]
    created_at: datetime


class ContentItemView(BaseSchema):
    id: int
    content_type: ContentType
    key: str
    display_name: str
    source_kind: ContentSourceKind
    status: ContentStatus
    tags: list[str]
    current_revision_id: int | None
    published_revision_id: int | None
    updated_by: str | None
    updated_at: datetime
    payload: dict[str, object] | None = None


class ContentDiffView(BaseSchema):
    from_version: int
    to_version: int
    before: dict[str, object]
    after: dict[str, object]


class BalanceItemView(BaseSchema):
    id: int
    key: str
    category: str
    scope: str
    enabled: bool
    value_json: dict[str, object]
    current_revision_id: int | None
    published_revision_id: int | None
    updated_at: datetime


class BalanceRevisionView(BaseSchema):
    id: int
    version: int
    change_summary: str
    is_published: bool
    published_at: datetime | None
    author_user_id: str | None
    value_json: dict[str, object]
    created_at: datetime


class AdminAuditLogView(BaseSchema):
    id: int
    actor_user_id: str | None
    action_type: str
    target_type: str
    target_id: str
    summary: str
    metadata_json: dict[str, object]
    created_at: datetime


class AdminUserView(BaseSchema):
    id: str
    username: str
    email: str
    roles: list[AdminRoleKey]


class AdminPlayerInventoryView(BaseSchema):
    resource: str
    amount: float


class AdminPlayerModuleView(BaseSchema):
    module_key: str
    level: int
    is_active: bool


class AdminPlayerSummaryView(BaseSchema):
    station_id: str
    owner_user_id: str
    username: str
    email: str
    is_active: bool
    station_name: str
    specialization: str
    level: int
    throughput: float
    efficiency: float
    stability: float
    reputation: float
    updated_at: datetime


class AdminPlayerDetailView(AdminPlayerSummaryView):
    public_notes: str
    inventories: list[AdminPlayerInventoryView]
    modules: list[AdminPlayerModuleView]
    last_processed_at: datetime


class AdminPlayerInventoryUpdate(BaseModel):
    resource: str
    amount: float = Field(ge=0, le=1_000_000_000)


class AdminPlayerModuleUpdate(BaseModel):
    module_key: str
    level: int = Field(ge=1, le=100)
    is_active: bool = True


class AdminPlayerUpdateRequest(BaseModel):
    station_name: str | None = Field(default=None, min_length=3, max_length=60)
    specialization: str | None = Field(default=None, min_length=2, max_length=40)
    level: int | None = Field(default=None, ge=1, le=10_000)
    throughput: float | None = Field(default=None, ge=0, le=1_000_000)
    efficiency: float | None = Field(default=None, ge=0, le=100)
    stability: float | None = Field(default=None, ge=0, le=100)
    reputation: float | None = Field(default=None, ge=0, le=100_000)
    public_notes: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None
    inventories: list[AdminPlayerInventoryUpdate] = Field(default_factory=list)
    modules: list[AdminPlayerModuleUpdate] = Field(default_factory=list)


class RoleAssignmentRequest(BaseModel):
    user_id: str
    roles: list[AdminRoleKey]


class ValidationIssue(BaseSchema):
    level: Literal["error", "warning"]
    field: str
    message: str


class ValidationResult(BaseSchema):
    valid: bool
    issues: list[ValidationIssue]


class AdminAuthzView(BaseSchema):
    user_id: str
    username: str
    roles: list[AdminRoleKey]
    permissions: list[str]
