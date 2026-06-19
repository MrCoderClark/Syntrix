"""add reputation and badges

Revision ID: f8b2c4d6e7a9
Revises: e7a1b2c3d4e5
Create Date: 2026-06-19 00:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f8b2c4d6e7a9"
down_revision: str | Sequence[str] | None = "e7a1b2c3d4e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Add reputation column to users ---
    op.add_column(
        "users",
        sa.Column("reputation", sa.Integer(), server_default=sa.text("0"), nullable=False),
        schema="syntrix",
    )

    # --- reputation_events table ---
    op.create_table(
        "reputation_events",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["syntrix.users.id"],
            name=op.f("fk_reputation_events_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reputation_events")),
        schema="syntrix",
    )
    op.create_index(
        "ix_reputation_events_user_id",
        "reputation_events",
        ["user_id"],
        schema="syntrix",
    )
    op.create_index(
        "ix_reputation_events_source_id",
        "reputation_events",
        ["source_id"],
        schema="syntrix",
    )

    # --- Trigger: reputation_events → users.reputation ---
    op.execute(
        """
        CREATE OR REPLACE FUNCTION syntrix.update_user_reputation()
        RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'INSERT' THEN
                UPDATE syntrix.users
                SET reputation = reputation + NEW.delta
                WHERE id = NEW.user_id;
                RETURN NEW;
            ELSIF TG_OP = 'DELETE' THEN
                UPDATE syntrix.users
                SET reputation = reputation - OLD.delta
                WHERE id = OLD.user_id;
                RETURN OLD;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_user_reputation
        AFTER INSERT OR DELETE ON syntrix.reputation_events
        FOR EACH ROW EXECUTE FUNCTION syntrix.update_user_reputation();
        """
    )

    # --- badges table ---
    op.create_table(
        "badges",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.Text(), nullable=True),
        sa.Column("tier", sa.Text(), nullable=False),
        sa.Column("criteria", sa.JSON(), nullable=False),
        sa.CheckConstraint(
            "tier IN ('bronze', 'silver', 'gold')",
            name="ck_badges_tier",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_badges")),
        sa.UniqueConstraint("slug", name="uq_badges_slug"),
        schema="syntrix",
    )

    # --- user_badges table ---
    op.create_table(
        "user_badges",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("badge_id", sa.UUID(), nullable=False),
        sa.Column(
            "awarded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["syntrix.users.id"],
            name=op.f("fk_user_badges_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["badge_id"],
            ["syntrix.badges.id"],
            name=op.f("fk_user_badges_badge_id_badges"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_badges")),
        sa.UniqueConstraint("user_id", "badge_id", name="uq_user_badges_user_badge"),
        schema="syntrix",
    )

    # --- Seed starter badges ---
    op.execute(
        """
        INSERT INTO syntrix.badges (slug, name, description, tier, criteria) VALUES
        (
            'first-question',
            'First Question',
            'Ask your first question',
            'bronze',
            '{"type": "question_count", "threshold": 1}'
        ),
        (
            'first-answer',
            'First Answer',
            'Post your first answer',
            'bronze',
            '{"type": "answer_count", "threshold": 1}'
        ),
        (
            'accepted',
            'Accepted',
            'Have an answer accepted',
            'bronze',
            '{"type": "accepted_answer_count", "threshold": 1}'
        ),
        (
            'scholar',
            'Scholar',
            'Accept an answer on your question',
            'bronze',
            '{"type": "questions_with_accepted", "threshold": 1}'
        ),
        (
            'nice-answer',
            'Nice Answer',
            'Answer with score >= 5',
            'bronze',
            '{"type": "answer_score_gte", "threshold": 5}'
        ),
        (
            'good-answer',
            'Good Answer',
            'Answer with score >= 25',
            'silver',
            '{"type": "answer_score_gte", "threshold": 25}'
        ),
        (
            'great-answer',
            'Great Answer',
            'Answer with score >= 100',
            'gold',
            '{"type": "answer_score_gte", "threshold": 100}'
        ),
        (
            'helpful',
            'Helpful',
            'First answer with score >= 1',
            'bronze',
            '{"type": "answer_score_gte", "threshold": 1}'
        ),
        (
            'curious',
            'Curious',
            'Ask 5 questions with score >= 1',
            'bronze',
            '{"type": "questions_with_score_gte", "threshold": 5, "min_score": 1}'
        ),
        (
            'inquisitive',
            'Inquisitive',
            'Ask 30 questions with score >= 1',
            'silver',
            '{"type": "questions_with_score_gte", "threshold": 30, "min_score": 1}'
        )
        ;
        """
    )


def downgrade() -> None:
    op.drop_table("user_badges", schema="syntrix")
    op.drop_table("badges", schema="syntrix")
    op.execute("DROP TRIGGER IF EXISTS trg_user_reputation ON syntrix.reputation_events")
    op.execute("DROP FUNCTION IF EXISTS syntrix.update_user_reputation()")
    op.drop_index(
        "ix_reputation_events_source_id", table_name="reputation_events", schema="syntrix"
    )
    op.drop_index("ix_reputation_events_user_id", table_name="reputation_events", schema="syntrix")
    op.drop_table("reputation_events", schema="syntrix")
    op.drop_column("users", "reputation", schema="syntrix")
