"""add chat_rooms and chat_messages

Revision ID: 84b1624e0064
Revises: 01ee0804de6a
Create Date: 2026-06-23 18:29:42.259923+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "84b1624e0064"
down_revision: str | Sequence[str] | None = "01ee0804de6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_rooms",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("community_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["syntrix.communities.id"],
            name=op.f("fk_chat_rooms_community_id_communities"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["syntrix.users.id"],
            name=op.f("fk_chat_rooms_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_rooms")),
        sa.UniqueConstraint("community_id", "slug", name=op.f("uq_chat_rooms_community_id")),
        schema="syntrix",
    )
    op.create_index(
        "ix_chat_rooms_community_id", "chat_rooms", ["community_id"], unique=False, schema="syntrix"
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=True),
        sa.Column("body_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["syntrix.users.id"],
            name=op.f("fk_chat_messages_author_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["syntrix.chat_rooms.id"],
            name=op.f("fk_chat_messages_room_id_chat_rooms"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_messages")),
        schema="syntrix",
    )
    op.create_index(
        "ix_chat_messages_room_created",
        "chat_messages",
        ["room_id", "created_at", "id"],
        unique=False,
        schema="syntrix",
    )


def downgrade() -> None:
    op.drop_index("ix_chat_messages_room_created", table_name="chat_messages", schema="syntrix")
    op.drop_table("chat_messages", schema="syntrix")
    op.drop_index("ix_chat_rooms_community_id", table_name="chat_rooms", schema="syntrix")
    op.drop_table("chat_rooms", schema="syntrix")
