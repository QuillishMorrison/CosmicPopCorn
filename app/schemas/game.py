from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema


class ResourceAmount(BaseSchema):
    resource: str
    amount: float


class ModuleView(BaseSchema):
    module_key: str
    level: int
    is_active: bool


class ModuleDefinitionView(BaseSchema):
    key: str
    name: str
    description: str
    category: str
    max_level: int
    base_cost: dict[str, float]
    upgrade_cost_growth: float
    energy_delta: float
    throughput_delta: float
    crew_requirement: int
    sort_order: int


class StationView(BaseSchema):
    id: str
    name: str
    level: int
    specialization: str
    throughput: float
    efficiency: float
    stability: float
    reputation: float
    bottlenecks: list[str]
    recommended_actions: list[str]
    inventories: list[ResourceAmount]
    modules: list[ModuleView]
    module_catalog: list[ModuleDefinitionView]
    last_processed_at: datetime


class StationRenameRequest(BaseModel):
    name: str = Field(min_length=3, max_length=60)


class ModuleActionRequest(BaseModel):
    module_key: str


class PolicyRequest(BaseModel):
    key: str
    value: str


class ReportView(BaseSchema):
    id: str
    started_at: datetime
    ended_at: datetime
    summary: dict[str, object]
    claimed_at: datetime | None


class MarketTradeRequest(BaseModel):
    resource: str
    quantity: float = Field(gt=0, le=9999)


class MarketStateView(BaseSchema):
    resource: str
    price: float
    trend: float
    history: list[float]


class ContractCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    contract_type: str
    resource: str
    quantity: float = Field(gt=0)
    reward_credits: float = Field(gt=0)


class TransferRequest(BaseModel):
    target_station_id: str
    resource: str
    amount: float = Field(gt=0)
    note: str = Field(default="", max_length=120)


class MetaUpgradeView(BaseSchema):
    key: str
    name: str
    description: str
    base_cost: int
    max_level: int
    effect_type: str
    effect_value: float
    current_level: int


class MetaPurchaseRequest(BaseModel):
    key: str


class NotificationView(BaseSchema):
    id: str
    type: str
    title: str
    message: str
    payload: dict[str, object]
    read_at: datetime | None


class ChatMessageView(BaseSchema):
    id: str
    sender_user_id: str
    sender_username: str
    recipient_user_id: str | None
    body: str
    created_at: datetime


class ChatThreadView(BaseSchema):
    user_id: str
    username: str
    station_name: str | None
    last_message: str | None
    last_message_at: datetime | None
    unread_count: int


class ChatSendRequest(BaseModel):
    body: str = Field(min_length=1, max_length=300)


class SectorPlayerView(BaseSchema):
    station_id: str
    station_name: str
    owner_username: str
    specialization: str
    level: int
    reputation: float


class SectorSnapshot(BaseSchema):
    sector_id: str
    sector_name: str
    market_mode: str
    market_mood: str
    players: list[SectorPlayerView]
    events: list[dict[str, object]]
