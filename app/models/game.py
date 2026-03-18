from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ContractStatus(str, Enum):
    open = "open"
    accepted = "accepted"
    completed = "completed"
    cancelled = "cancelled"


class ContractSource(str, Enum):
    npc = "npc"
    player = "player"


class NotificationType(str, Enum):
    report = "report"
    market = "market"
    contract = "contract"
    security = "security"
    system = "system"


class AdminRoleKey(str, Enum):
    super_admin = "super_admin"
    admin = "admin"
    designer = "designer"
    moderator = "moderator"


class ContentType(str, Enum):
    resource = "resource"
    module = "module"
    event = "event"
    contract_template = "contract_template"
    meta_upgrade = "meta_upgrade"
    specialization = "specialization"


class ContentStatus(str, Enum):
    draft = "draft"
    active = "active"
    disabled = "disabled"
    archived = "archived"


class ContentSourceKind(str, Enum):
    system = "system"
    admin = "admin"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    station: Mapped["Station | None"] = relationship(back_populates="owner", uselist=False)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    meta_progress: Mapped[list["UserMetaProgress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = (Index("ix_refresh_tokens_user_active", "user_id", "revoked_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rotated_from_id: Mapped[str | None] = mapped_column(ForeignKey("refresh_tokens.id"), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class AuthAttempt(TimestampMixin, Base):
    __tablename__ = "auth_attempts"
    __table_args__ = (
        Index("ix_auth_attempts_ip_created", "ip_address", "created_at"),
        Index("ix_auth_attempts_identity_created", "identity", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    identity: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(50), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SecurityLog(TimestampMixin, Base):
    __tablename__ = "security_logs"
    __table_args__ = (Index("ix_security_logs_user_event", "user_id", "event_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    detail: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class Sector(TimestampMixin, Base):
    __tablename__ = "sectors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    market_mode: Mapped[str] = mapped_column(String(30), default="balanced", nullable=False)
    market_mood: Mapped[str] = mapped_column(
        String(120), default="Stable flows, narrow spreads.", nullable=False
    )
    tick_seed: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    stations: Mapped[list["Station"]] = relationship(back_populates="sector")
    market_states: Mapped[list["MarketState"]] = relationship(
        back_populates="sector", cascade="all, delete-orphan"
    )
    world_events: Mapped[list["WorldEvent"]] = relationship(
        back_populates="sector", cascade="all, delete-orphan"
    )


class Station(TimestampMixin, Base):
    __tablename__ = "stations"
    __table_args__ = (
        UniqueConstraint("owner_id", name="uq_stations_owner_id"),
        Index("ix_stations_sector_specialization", "sector_id", "specialization"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sector_id: Mapped[str] = mapped_column(ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    specialization: Mapped[str] = mapped_column(String(30), default="freight_hub", nullable=False)
    throughput: Mapped[float] = mapped_column(Float, default=12.0, nullable=False)
    efficiency: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    stability: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    reputation: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    policy_config: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    public_notes: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    last_processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_report_claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="station")
    sector: Mapped["Sector"] = relationship(back_populates="stations")
    modules: Mapped[list["StationModule"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )
    inventories: Mapped[list["Inventory"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )
    reports: Mapped[list["DailyReport"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )
    policies: Mapped[list["PolicyConfig"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )
    research_queue: Mapped[list["ResearchQueue"]] = relationship(
        back_populates="station", cascade="all, delete-orphan"
    )


class Inventory(TimestampMixin, Base):
    __tablename__ = "inventories"
    __table_args__ = (
        UniqueConstraint("station_id", "resource", name="uq_inventories_station_resource"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    resource: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    station: Mapped["Station"] = relationship(back_populates="inventories")


class StationModule(TimestampMixin, Base):
    __tablename__ = "station_modules"
    __table_args__ = (
        UniqueConstraint("station_id", "module_key", name="uq_station_modules_station_module"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    module_key: Mapped[str] = mapped_column(String(40), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    station: Mapped["Station"] = relationship(back_populates="modules")


class MetaUpgrade(TimestampMixin, Base):
    __tablename__ = "meta_upgrades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    base_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    max_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    effect_type: Mapped[str] = mapped_column(String(40), nullable=False)
    effect_value: Mapped[float] = mapped_column(Float, nullable=False)


class UserMetaProgress(TimestampMixin, Base):
    __tablename__ = "user_meta_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "upgrade_id", name="uq_user_meta_progress_user_upgrade"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    upgrade_id: Mapped[int] = mapped_column(
        ForeignKey("meta_upgrades.id", ondelete="CASCADE"), nullable=False
    )
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="meta_progress")
    upgrade: Mapped["MetaUpgrade"] = relationship()


class Contract(TimestampMixin, Base):
    __tablename__ = "contracts"
    __table_args__ = (
        Index("ix_contracts_sector_status", "sector_id", "status"),
        CheckConstraint("quantity > 0", name="contracts_quantity_positive"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sector_id: Mapped[str] = mapped_column(ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False)
    issuer_station_id: Mapped[str | None] = mapped_column(
        ForeignKey("stations.id", ondelete="SET NULL"), nullable=True
    )
    taker_station_id: Mapped[str | None] = mapped_column(
        ForeignKey("stations.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[ContractSource] = mapped_column(
        SqlEnum(ContractSource), default=ContractSource.npc, nullable=False
    )
    status: Mapped[ContractStatus] = mapped_column(
        SqlEnum(ContractStatus), default=ContractStatus.open, nullable=False
    )
    contract_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    resource: Mapped[str] = mapped_column(String(30), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    reward_credits: Mapped[float] = mapped_column(Float, nullable=False)
    reward_reputation: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MarketState(TimestampMixin, Base):
    __tablename__ = "market_states"
    __table_args__ = (UniqueConstraint("sector_id", "resource", name="uq_market_states_sector_resource"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sector_id: Mapped[str] = mapped_column(ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False)
    resource: Mapped[str] = mapped_column(String(30), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    trend: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    history: Mapped[list[float]] = mapped_column(JSON, default=list, nullable=False)

    sector: Mapped["Sector"] = relationship(back_populates="market_states")


class MarketTransaction(TimestampMixin, Base):
    __tablename__ = "market_transactions"
    __table_args__ = (Index("ix_market_transactions_station_created", "station_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    sector_id: Mapped[str] = mapped_column(ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False)
    resource: Mapped[str] = mapped_column(String(30), nullable=False)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)


class PlayerTransfer(TimestampMixin, Base):
    __tablename__ = "player_transfers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_station_id: Mapped[str] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"), nullable=False
    )
    to_station_id: Mapped[str] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    resource: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str] = mapped_column(String(120), default="", nullable=False)


class WorldEvent(TimestampMixin, Base):
    __tablename__ = "world_events"
    __table_args__ = (Index("ix_world_events_sector_active", "sector_id", "ends_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sector_id: Mapped[str] = mapped_column(ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    market_effects: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sector: Mapped["Sector"] = relationship(back_populates="world_events")


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read", "user_id", "read_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[NotificationType] = mapped_column(SqlEnum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(String(300), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ChatMessage(TimestampMixin, Base):
    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_global_created", "recipient_user_id", "created_at"),
        Index("ix_chat_messages_sender_created", "sender_user_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    body: Mapped[str] = mapped_column(String(300), nullable=False)


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[AdminRoleKey] = mapped_column(SqlEnum(AdminRoleKey), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    users: Mapped[list["UserRole"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class UserRole(TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="roles")
    role: Mapped["Role"] = relationship(back_populates="users")


class GameContentItem(TimestampMixin, Base):
    __tablename__ = "game_content_items"
    __table_args__ = (
        UniqueConstraint("content_type", "key", name="uq_game_content_items_type_key"),
        Index("ix_game_content_items_type_status", "content_type", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_type: Mapped[ContentType] = mapped_column(SqlEnum(ContentType), nullable=False)
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    source_kind: Mapped[ContentSourceKind] = mapped_column(
        SqlEnum(ContentSourceKind), default=ContentSourceKind.admin, nullable=False
    )
    status: Mapped[ContentStatus] = mapped_column(SqlEnum(ContentStatus), default=ContentStatus.draft, nullable=False)
    base_ref: Mapped[str | None] = mapped_column(String(80), nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    current_revision_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    published_revision_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    revisions: Mapped[list["GameContentRevision"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="GameContentRevision.version"
    )


class GameContentRevision(TimestampMixin, Base):
    __tablename__ = "game_content_revisions"
    __table_args__ = (UniqueConstraint("content_item_id", "version", name="uq_game_content_revisions_item_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content_item_id: Mapped[int] = mapped_column(
        ForeignKey("game_content_items.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    change_summary: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    author_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    item: Mapped["GameContentItem"] = relationship(back_populates="revisions")


class BalanceParameter(TimestampMixin, Base):
    __tablename__ = "balance_parameters"
    __table_args__ = (UniqueConstraint("key", name="uq_balance_parameters_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    scope: Mapped[str] = mapped_column(String(40), default="global", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    value_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    current_revision_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    published_revision_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    revisions: Mapped[list["BalanceRevision"]] = relationship(
        back_populates="parameter", cascade="all, delete-orphan", order_by="BalanceRevision.version"
    )


class BalanceRevision(TimestampMixin, Base):
    __tablename__ = "balance_revisions"
    __table_args__ = (UniqueConstraint("balance_parameter_id", "version", name="uq_balance_revisions_param_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    balance_parameter_id: Mapped[int] = mapped_column(
        ForeignKey("balance_parameters.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    value_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    change_summary: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    author_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    parameter: Mapped["BalanceParameter"] = relationship(back_populates="revisions")


class AdminAuditLog(TimestampMixin, Base):
    __tablename__ = "admin_audit_logs"
    __table_args__ = (
        Index("ix_admin_audit_logs_actor_created", "actor_user_id", "created_at"),
        Index("ix_admin_audit_logs_target", "target_type", "target_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_id: Mapped[str] = mapped_column(String(80), nullable=False)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)


class DailyReport(TimestampMixin, Base):
    __tablename__ = "daily_reports"
    __table_args__ = (Index("ix_daily_reports_station_claimed", "station_id", "claimed_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    station: Mapped["Station"] = relationship(back_populates="reports")


class PolicyConfig(TimestampMixin, Base):
    __tablename__ = "policy_configs"
    __table_args__ = (UniqueConstraint("station_id", "key", name="uq_policy_configs_station_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(40), nullable=False)
    value: Mapped[str] = mapped_column(String(80), nullable=False)

    station: Mapped["Station"] = relationship(back_populates="policies")


class ResearchQueue(TimestampMixin, Base):
    __tablename__ = "research_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    meta_upgrade_key: Mapped[str] = mapped_column(String(40), nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    station: Mapped["Station"] = relationship(back_populates="research_queue")
