"""community tables

Revision ID: 0003_community_tables
Revises: 0002_auth_tables
Create Date: 2026-06-17 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_community_tables"
down_revision: str | Sequence[str] | None = "0002_auth_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "communities",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("slug", postgresql.CITEXT(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.Text(), nullable=False, server_default="#1e3a5f"),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["syntrix.users.id"],
            name=op.f("fk_communities_owner_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_communities")),
        sa.UniqueConstraint("slug", name=op.f("uq_communities_slug")),
        schema="syntrix",
    )

    op.create_table(
        "community_memberships",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("community_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="member"),
        sa.Column("banned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ban_reason", sa.Text(), nullable=True),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["syntrix.communities.id"],
            name=op.f("fk_community_memberships_community_id_communities"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["syntrix.users.id"],
            name=op.f("fk_community_memberships_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_community_memberships")),
        sa.UniqueConstraint(
            "community_id", "user_id", name="uq_community_memberships_community_user"
        ),
        schema="syntrix",
    )

    op.create_table(
        "community_requests",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("requested_by", sa.UUID(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("reviewed_by", sa.UUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["syntrix.users.id"],
            name=op.f("fk_community_requests_requested_by_users"),
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["syntrix.users.id"],
            name=op.f("fk_community_requests_reviewed_by_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_community_requests")),
        schema="syntrix",
    )


def downgrade() -> None:
    op.drop_table("community_requests", schema="syntrix")
    op.drop_table("community_memberships", schema="syntrix")
    op.drop_table("communities", schema="syntrix")
