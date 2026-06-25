"""add private rooms, DMs, chat_room_members, and invites

Revision ID: 55327d4afc2d
Revises: 84b1624e0064
Create Date: 2026-06-23 20:25:18.796649+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "55327d4afc2d"
down_revision: str | Sequence[str] | None = "84b1624e0064"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create invites table
    op.create_table(
        "invites",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("target_type", sa.Text(), nullable=False),
        sa.Column("target_id", sa.UUID(), nullable=False),
        sa.Column("invited_by", sa.UUID(), nullable=False),
        sa.Column("invited_user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["invited_by"],
            ["syntrix.users.id"],
            name=op.f("fk_invites_invited_by_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["invited_user_id"],
            ["syntrix.users.id"],
            name=op.f("fk_invites_invited_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_invites")),
        sa.UniqueConstraint(
            "target_type", "target_id", "invited_user_id", name=op.f("uq_invites_target_type")
        ),
        schema="syntrix",
    )
    op.create_index(
        "ix_invites_invited_user",
        "invites",
        ["invited_user_id", "status"],
        unique=False,
        schema="syntrix",
    )

    # Create chat_room_members table
    op.create_table(
        "chat_room_members",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("added_by", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["added_by"],
            ["syntrix.users.id"],
            name=op.f("fk_chat_room_members_added_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["syntrix.chat_rooms.id"],
            name=op.f("fk_chat_room_members_room_id_chat_rooms"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["syntrix.users.id"],
            name=op.f("fk_chat_room_members_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_room_members")),
        sa.UniqueConstraint("room_id", "user_id", name=op.f("uq_chat_room_members_room_id")),
        schema="syntrix",
    )
    op.create_index(
        "ix_chat_room_members_user_id",
        "chat_room_members",
        ["user_id"],
        unique=False,
        schema="syntrix",
    )

    # Add is_private and is_dm to chat_rooms; make community_id nullable for DMs
    op.add_column(
        "chat_rooms",
        sa.Column("is_private", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        schema="syntrix",
    )
    op.add_column(
        "chat_rooms",
        sa.Column("is_dm", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        schema="syntrix",
    )
    op.alter_column(
        "chat_rooms", "community_id", existing_type=sa.UUID(), nullable=True, schema="syntrix"
    )

    # Add is_private to communities
    op.add_column(
        "communities",
        sa.Column("is_private", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        schema="syntrix",
    )


def downgrade() -> None:
    op.drop_column("communities", "is_private", schema="syntrix")

    op.alter_column(
        "chat_rooms", "community_id", existing_type=sa.UUID(), nullable=False, schema="syntrix"
    )
    op.drop_column("chat_rooms", "is_dm", schema="syntrix")
    op.drop_column("chat_rooms", "is_private", schema="syntrix")

    op.drop_index("ix_chat_room_members_user_id", table_name="chat_room_members", schema="syntrix")
    op.drop_table("chat_room_members", schema="syntrix")
    op.drop_index("ix_invites_invited_user", table_name="invites", schema="syntrix")
    op.drop_table("invites", schema="syntrix")
