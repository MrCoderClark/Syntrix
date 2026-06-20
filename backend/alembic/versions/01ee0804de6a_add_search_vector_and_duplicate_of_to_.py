"""add search_vector and duplicate_of to posts

Revision ID: 01ee0804de6a
Revises: f8b2c4d6e7a9
Create Date: 2026-06-20 18:51:02.146241+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

from alembic import op

revision: str = "01ee0804de6a"
down_revision: str | Sequence[str] | None = "f8b2c4d6e7a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Ensure pg_trgm extension is available ---
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # --- Add search_vector column ---
    op.add_column(
        "posts",
        sa.Column("search_vector", TSVECTOR(), nullable=True),
        schema="syntrix",
    )

    # --- Add duplicate_of_id column ---
    op.add_column(
        "posts",
        sa.Column("duplicate_of_id", sa.UUID(), nullable=True),
        schema="syntrix",
    )
    op.create_foreign_key(
        op.f("fk_posts_duplicate_of_id_posts"),
        "posts",
        "posts",
        ["duplicate_of_id"],
        ["id"],
        source_schema="syntrix",
        referent_schema="syntrix",
        ondelete="SET NULL",
    )

    # --- GIN index on search_vector ---
    op.create_index(
        "ix_posts_search_vector",
        "posts",
        ["search_vector"],
        schema="syntrix",
        postgresql_using="gin",
    )

    # --- GIN trigram index on title ---
    op.execute(
        "CREATE INDEX ix_posts_title_trgm ON syntrix.posts " "USING gin (title gin_trgm_ops)"
    )

    # --- PL/pgSQL function to extract text from body_json ---
    op.execute(
        """
        CREATE OR REPLACE FUNCTION syntrix.extract_tiptap_text(doc jsonb)
        RETURNS text AS $$
        DECLARE
            node jsonb;
            result text := '';
        BEGIN
            IF doc ? 'text' AND (doc ->> 'type') = 'text' THEN
                result := result || (doc ->> 'text') || ' ';
            END IF;
            IF doc ? 'content' THEN
                FOR node IN SELECT jsonb_array_elements(doc -> 'content')
                LOOP
                    result := result || syntrix.extract_tiptap_text(node);
                END LOOP;
            END IF;
            RETURN result;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """
    )

    # --- Trigger function to update search_vector ---
    op.execute(
        """
        CREATE OR REPLACE FUNCTION syntrix.posts_search_vector_update()
        RETURNS trigger AS $$
        DECLARE
            body_text text;
        BEGIN
            body_text := coalesce(syntrix.extract_tiptap_text(NEW.body_json), '');
            NEW.search_vector :=
                setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
                setweight(to_tsvector('english', body_text), 'B');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # --- Trigger on INSERT/UPDATE ---
    op.execute(
        """
        CREATE TRIGGER trg_posts_search_vector
        BEFORE INSERT OR UPDATE OF title, body_json ON syntrix.posts
        FOR EACH ROW EXECUTE FUNCTION syntrix.posts_search_vector_update();
        """
    )

    # --- Backfill existing posts ---
    op.execute(
        """
        UPDATE syntrix.posts SET
            search_vector =
                setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('english',
                    coalesce(syntrix.extract_tiptap_text(body_json), '')), 'B');
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_posts_search_vector ON syntrix.posts")
    op.execute("DROP FUNCTION IF EXISTS syntrix.posts_search_vector_update()")
    op.execute("DROP FUNCTION IF EXISTS syntrix.extract_tiptap_text(jsonb)")
    op.execute("DROP INDEX IF EXISTS syntrix.ix_posts_title_trgm")
    op.drop_index("ix_posts_search_vector", table_name="posts", schema="syntrix")
    op.drop_constraint(
        op.f("fk_posts_duplicate_of_id_posts"), "posts", schema="syntrix", type_="foreignkey"
    )
    op.drop_column("posts", "duplicate_of_id", schema="syntrix")
    op.drop_column("posts", "search_vector", schema="syntrix")
