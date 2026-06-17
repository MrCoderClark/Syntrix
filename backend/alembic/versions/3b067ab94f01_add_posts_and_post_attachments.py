"""add posts and post_attachments

Revision ID: 3b067ab94f01
Revises: 0003_community_tables
Create Date: 2026-06-17 15:51:03.616989+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "3b067ab94f01"
down_revision: str | Sequence[str] | None = "0003_community_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "posts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("community_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("comment_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_pinned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_by", sa.UUID(), nullable=True),
        sa.Column("removed_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["syntrix.users.id"],
            name=op.f("fk_posts_author_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["syntrix.communities.id"],
            name=op.f("fk_posts_community_id_communities"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["removed_by"],
            ["syntrix.users.id"],
            name=op.f("fk_posts_removed_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_posts")),
        schema="syntrix",
    )
    op.create_table(
        "post_attachments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.UUID(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["syntrix.posts.id"],
            name=op.f("fk_post_attachments_post_id_posts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_post_attachments")),
        schema="syntrix",
    )


def downgrade() -> None:
    op.drop_table("post_attachments", schema="syntrix")
    op.drop_table("posts", schema="syntrix")
