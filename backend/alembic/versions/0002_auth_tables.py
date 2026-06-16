"""auth tables

Revision ID: 0002_auth_tables
Revises: 0001_baseline
Create Date: 2026-06-16 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_auth_tables"
down_revision: str | Sequence[str] | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("handle", postgresql.CITEXT(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("audience_tag", sa.Text(), nullable=True),
        sa.Column("role", sa.Text(), nullable=False, server_default="member"),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("handle", name=op.f("uq_users_handle")),
        schema="syntrix",
    )

    op.create_table(
        "oauth_identities",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("provider_sub", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["syntrix.users.id"],
            name=op.f("fk_oauth_identities_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_oauth_identities")),
        sa.UniqueConstraint("provider", "provider_sub", name="uq_oauth_identities_provider_sub"),
        schema="syntrix",
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["syntrix.users.id"],
            name=op.f("fk_refresh_tokens_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
        schema="syntrix",
    )
    op.create_index(
        "ix_refresh_tokens_user_active",
        "refresh_tokens",
        ["user_id"],
        schema="syntrix",
        postgresql_where=sa.text("revoked_at IS NULL"),
    )

    op.create_table(
        "rate_limit_buckets",
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("tokens", sa.Numeric(), nullable=False),
        sa.Column("max_tokens", sa.Numeric(), nullable=False),
        sa.Column("refill_rate", sa.Numeric(), nullable=False),
        sa.Column(
            "refilled_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_rate_limit_buckets")),
        schema="syntrix",
    )


def downgrade() -> None:
    op.drop_table("rate_limit_buckets", schema="syntrix")
    op.drop_index(
        "ix_refresh_tokens_user_active",
        table_name="refresh_tokens",
        schema="syntrix",
    )
    op.drop_table("refresh_tokens", schema="syntrix")
    op.drop_table("oauth_identities", schema="syntrix")
    op.drop_table("users", schema="syntrix")
