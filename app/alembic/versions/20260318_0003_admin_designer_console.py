"""admin designer console"""

from alembic import op
import sqlalchemy as sa


revision = "20260318_0003"
down_revision = "20260318_0002"
branch_labels = None
depends_on = None


admin_role_enum = sa.Enum("super_admin", "admin", "designer", "moderator", name="adminrolekey")
content_type_enum = sa.Enum(
    "resource",
    "module",
    "event",
    "contract_template",
    "meta_upgrade",
    "specialization",
    name="contenttype",
)
content_status_enum = sa.Enum("draft", "active", "disabled", "archived", name="contentstatus")
content_source_enum = sa.Enum("system", "admin", name="contentsourcekind")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    admin_role_enum.create(bind, checkfirst=True)
    content_type_enum.create(bind, checkfirst=True)
    content_status_enum.create(bind, checkfirst=True)
    content_source_enum.create(bind, checkfirst=True)

    if "roles" not in tables:
        op.create_table(
            "roles",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("key", admin_role_enum, nullable=False),
            sa.Column("name", sa.String(length=60), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("key", name="uq_roles_key"),
        )

    if "user_roles" not in tables:
        op.create_table(
            "user_roles",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        )

    if "game_content_items" not in tables:
        op.create_table(
            "game_content_items",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("content_type", content_type_enum, nullable=False),
            sa.Column("key", sa.String(length=80), nullable=False),
            sa.Column("display_name", sa.String(length=120), nullable=False, server_default=""),
            sa.Column("source_kind", content_source_enum, nullable=False, server_default="admin"),
            sa.Column("status", content_status_enum, nullable=False, server_default="draft"),
            sa.Column("base_ref", sa.String(length=80), nullable=True),
            sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("current_revision_id", sa.Integer(), nullable=True),
            sa.Column("published_revision_id", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("updated_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("content_type", "key", name="uq_game_content_items_type_key"),
        )
        op.create_index(
            "ix_game_content_items_type_status",
            "game_content_items",
            ["content_type", "status"],
            unique=False,
        )

    if "game_content_revisions" not in tables:
        op.create_table(
            "game_content_revisions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "content_item_id",
                sa.Integer(),
                sa.ForeignKey("game_content_items.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("payload_json", sa.JSON(), nullable=False),
            sa.Column("change_summary", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("author_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("content_item_id", "version", name="uq_game_content_revisions_item_version"),
        )

    if "balance_parameters" not in tables:
        op.create_table(
            "balance_parameters",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("key", sa.String(length=80), nullable=False),
            sa.Column("category", sa.String(length=80), nullable=False),
            sa.Column("scope", sa.String(length=40), nullable=False, server_default="global"),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("value_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("current_revision_id", sa.Integer(), nullable=True),
            sa.Column("published_revision_id", sa.Integer(), nullable=True),
            sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("updated_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("key", name="uq_balance_parameters_key"),
        )

    if "balance_revisions" not in tables:
        op.create_table(
            "balance_revisions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "balance_parameter_id",
                sa.Integer(),
                sa.ForeignKey("balance_parameters.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("value_json", sa.JSON(), nullable=False),
            sa.Column("change_summary", sa.String(length=255), nullable=False, server_default=""),
            sa.Column("author_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("balance_parameter_id", "version", name="uq_balance_revisions_param_version"),
        )

    if "admin_audit_logs" not in tables:
        op.create_table(
            "admin_audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("actor_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("action_type", sa.String(length=80), nullable=False),
            sa.Column("target_type", sa.String(length=80), nullable=False),
            sa.Column("target_id", sa.String(length=80), nullable=False),
            sa.Column("summary", sa.String(length=255), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index(
            "ix_admin_audit_logs_actor_created",
            "admin_audit_logs",
            ["actor_user_id", "created_at"],
            unique=False,
        )
        op.create_index(
            "ix_admin_audit_logs_target",
            "admin_audit_logs",
            ["target_type", "target_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()

    for index_name, table_name in [
        ("ix_admin_audit_logs_target", "admin_audit_logs"),
        ("ix_admin_audit_logs_actor_created", "admin_audit_logs"),
        ("ix_game_content_items_type_status", "game_content_items"),
    ]:
        try:
            op.drop_index(index_name, table_name=table_name)
        except Exception:
            pass

    for table_name in [
        "admin_audit_logs",
        "balance_revisions",
        "balance_parameters",
        "game_content_revisions",
        "game_content_items",
        "user_roles",
        "roles",
    ]:
        try:
            op.drop_table(table_name)
        except Exception:
            pass

    content_source_enum.drop(bind, checkfirst=True)
    content_status_enum.drop(bind, checkfirst=True)
    content_type_enum.drop(bind, checkfirst=True)
    admin_role_enum.drop(bind, checkfirst=True)
