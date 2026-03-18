"""chat media support"""

from alembic import op
import sqlalchemy as sa


revision = "20260318_0002"
down_revision = "20260318_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "chat_messages" not in tables:
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.String(length=36), primary_key=True),
            sa.Column("sender_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("recipient_user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
            sa.Column("body", sa.String(length=300), nullable=False),
            sa.Column("image_url", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_chat_messages_global_created", "chat_messages", ["recipient_user_id", "created_at"], unique=False)
        op.create_index("ix_chat_messages_sender_created", "chat_messages", ["sender_user_id", "created_at"], unique=False)
        return

    columns = {column["name"] for column in inspector.get_columns("chat_messages")}
    if "image_url" not in columns:
        op.add_column("chat_messages", sa.Column("image_url", sa.String(length=255), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "chat_messages" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("chat_messages")}
    if "image_url" in columns:
        op.drop_column("chat_messages", "image_url")
