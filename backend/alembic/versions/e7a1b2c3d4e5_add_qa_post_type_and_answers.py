"""add qa post type and answers

Revision ID: e7a1b2c3d4e5
Revises: d49e5736632d
Create Date: 2026-06-18 00:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e7a1b2c3d4e5"
down_revision: str | Sequence[str] | None = "d49e5736632d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Extend posts table ---
    op.add_column(
        "posts",
        sa.Column(
            "post_type",
            sa.Text(),
            server_default=sa.text("'discussion'"),
            nullable=False,
        ),
        schema="syntrix",
    )
    op.execute(
        "ALTER TABLE syntrix.posts ADD CONSTRAINT ck_posts_post_type "
        "CHECK (post_type IN ('discussion', 'question'))"
    )
    op.add_column(
        "posts",
        sa.Column("answer_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        schema="syntrix",
    )
    op.add_column(
        "posts",
        sa.Column(
            "has_accepted_answer",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        schema="syntrix",
    )

    # --- Answers table ---
    op.create_table(
        "answers",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("question_id", sa.UUID(), nullable=False),
        sa.Column("author_id", sa.UUID(), nullable=True),
        sa.Column("body_json", sa.JSON(), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=False),
        sa.Column("score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_accepted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
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
            ["question_id"],
            ["syntrix.posts.id"],
            name=op.f("fk_answers_question_id_posts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["syntrix.users.id"],
            name=op.f("fk_answers_author_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["removed_by"],
            ["syntrix.users.id"],
            name=op.f("fk_answers_removed_by_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_answers")),
        schema="syntrix",
    )

    # --- Answer votes table ---
    op.create_table(
        "answer_votes",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("answer_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("value", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["answer_id"],
            ["syntrix.answers.id"],
            name=op.f("fk_answer_votes_answer_id_answers"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["syntrix.users.id"],
            name=op.f("fk_answer_votes_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_answer_votes")),
        sa.UniqueConstraint("answer_id", "user_id", name="uq_answer_votes_answer_user"),
        sa.CheckConstraint("value IN (-1, 1)", name="ck_answer_votes_value"),
        schema="syntrix",
    )

    # --- Trigger: answer_votes → answers.score ---
    op.execute(
        """
        CREATE OR REPLACE FUNCTION syntrix.update_answer_score()
        RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE syntrix.answers SET score = score + NEW.value WHERE id = NEW.answer_id;
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE syntrix.answers SET score = score - OLD.value WHERE id = OLD.answer_id;
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                UPDATE syntrix.answers
                SET score = score - OLD.value + NEW.value
                WHERE id = NEW.answer_id;
                RETURN NEW;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
    """
    )
    op.execute(
        """
        CREATE TRIGGER trg_answer_score
        AFTER INSERT OR UPDATE OR DELETE ON syntrix.answer_votes
        FOR EACH ROW EXECUTE FUNCTION syntrix.update_answer_score();
    """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_answer_score ON syntrix.answer_votes")
    op.execute("DROP FUNCTION IF EXISTS syntrix.update_answer_score()")
    op.drop_table("answer_votes", schema="syntrix")
    op.drop_table("answers", schema="syntrix")
    op.drop_column("posts", "has_accepted_answer", schema="syntrix")
    op.drop_column("posts", "answer_count", schema="syntrix")
    op.execute("ALTER TABLE syntrix.posts DROP CONSTRAINT IF EXISTS ck_posts_post_type")
    op.drop_column("posts", "post_type", schema="syntrix")
