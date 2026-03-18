"""initial schema"""

from alembic import op
import sqlalchemy as sa


revision = "20260318_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=32), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "sectors",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("market_mode", sa.String(length=30), nullable=False, server_default="balanced"),
        sa.Column("market_mood", sa.String(length=120), nullable=False, server_default="Stable flows, narrow spreads."),
        sa.Column("tick_seed", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_sectors_name"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated_from_id", sa.String(length=36), sa.ForeignKey("refresh_tokens.id")),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("user_agent", sa.String(length=255)),
        sa.Column("ip_address", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_active", "refresh_tokens", ["user_id", "revoked_at"], unique=False)

    op.create_table(
        "auth_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("identity", sa.String(length=255), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("endpoint", sa.String(length=50), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_auth_attempts_identity", "auth_attempts", ["identity"], unique=False)
    op.create_index("ix_auth_attempts_ip_created", "auth_attempts", ["ip_address", "created_at"], unique=False)
    op.create_index("ix_auth_attempts_identity_created", "auth_attempts", ["identity", "created_at"], unique=False)

    op.create_table(
        "security_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("ip_address", sa.String(length=64)),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_security_logs_user_event", "security_logs", ["user_id", "event_type"], unique=False)

    op.create_table(
        "stations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("owner_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sector_id", sa.String(length=36), sa.ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("specialization", sa.String(length=30), nullable=False, server_default="freight_hub"),
        sa.Column("throughput", sa.Float(), nullable=False, server_default="12"),
        sa.Column("efficiency", sa.Float(), nullable=False, server_default="1"),
        sa.Column("stability", sa.Float(), nullable=False, server_default="100"),
        sa.Column("reputation", sa.Float(), nullable=False, server_default="0"),
        sa.Column("policy_config", sa.JSON(), nullable=False),
        sa.Column("public_notes", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("last_processed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_report_claimed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("owner_id", name="uq_stations_owner_id"),
    )
    op.create_index("ix_stations_sector_specialization", "stations", ["sector_id", "specialization"], unique=False)

    op.create_table(
        "inventories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("station_id", sa.String(length=36), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("station_id", "resource", name="uq_inventories_station_resource"),
    )

    op.create_table(
        "station_modules",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("station_id", sa.String(length=36), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_key", sa.String(length=40), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("station_id", "module_key", name="uq_station_modules_station_module"),
    )

    op.create_table(
        "meta_upgrades",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=False),
        sa.Column("base_cost", sa.Integer(), nullable=False),
        sa.Column("max_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("effect_type", sa.String(length=40), nullable=False),
        sa.Column("effect_value", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("key", name="uq_meta_upgrades_key"),
    )

    op.create_table(
        "user_meta_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("upgrade_id", sa.Integer(), sa.ForeignKey("meta_upgrades.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "upgrade_id", name="uq_user_meta_progress_user_upgrade"),
    )

    op.create_table(
        "contracts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("sector_id", sa.String(length=36), sa.ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issuer_station_id", sa.String(length=36), sa.ForeignKey("stations.id", ondelete="SET NULL")),
        sa.Column("taker_station_id", sa.String(length=36), sa.ForeignKey("stations.id", ondelete="SET NULL")),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("contract_type", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("resource", sa.String(length=30), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("reward_credits", sa.Float(), nullable=False),
        sa.Column("reward_reputation", sa.Float(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="contracts_quantity_positive"),
    )
    op.create_index("ix_contracts_sector_status", "contracts", ["sector_id", "status"], unique=False)

    op.create_table(
        "market_states",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sector_id", sa.String(length=36), sa.ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource", sa.String(length=30), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("trend", sa.Float(), nullable=False, server_default="0"),
        sa.Column("history", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("sector_id", "resource", name="uq_market_states_sector_resource"),
    )

    op.create_table(
        "market_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("station_id", sa.String(length=36), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sector_id", sa.String(length=36), sa.ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource", sa.String(length=30), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_market_transactions_station_created", "market_transactions", ["station_id", "created_at"], unique=False)

    op.create_table(
        "player_transfers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("from_station_id", sa.String(length=36), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_station_id", sa.String(length=36), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("note", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "world_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("sector_id", sa.String(length=36), sa.ForeignKey("sectors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("market_effects", sa.JSON(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_world_events_sector_active", "world_events", ["sector_id", "ends_at"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("message", sa.String(length=300), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read_at"], unique=False)

    op.create_table(
        "daily_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("station_id", sa.String(length=36), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_daily_reports_station_claimed", "daily_reports", ["station_id", "claimed_at"], unique=False)

    op.create_table(
        "policy_configs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("station_id", sa.String(length=36), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(length=40), nullable=False),
        sa.Column("value", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("station_id", "key", name="uq_policy_configs_station_key"),
    )

    op.create_table(
        "research_queue",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("station_id", sa.String(length=36), sa.ForeignKey("stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meta_upgrade_key", sa.String(length=40), nullable=False),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "research_queue",
        "policy_configs",
        "daily_reports",
        "notifications",
        "world_events",
        "player_transfers",
        "market_transactions",
        "market_states",
        "contracts",
        "user_meta_progress",
        "meta_upgrades",
        "station_modules",
        "inventories",
        "stations",
        "security_logs",
        "auth_attempts",
        "refresh_tokens",
        "sectors",
        "users",
    ]:
        op.drop_table(table)
