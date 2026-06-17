"""add comments table

Revision ID: 10adf492c474
Revises: 3b067ab94f01
Create Date: 2026-06-17 17:12:19.280877+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "10adf492c474"
down_revision: str | Sequence[str] | None = "3b067ab94f01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("post_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=True),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("body_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), server_default=sa.text("0"), nullable=False),
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
            name=op.f("fk_comments_author_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["syntrix.comments.id"],
            name=op.f("fk_comments_parent_id_comments"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["syntrix.posts.id"],
            name=op.f("fk_comments_post_id_posts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["removed_by"],
            ["syntrix.users.id"],
            name=op.f("fk_comments_removed_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_comments")),
        schema="syntrix",
    )


def downgrade() -> None:
    op.drop_table("comments", schema="syntrix")
