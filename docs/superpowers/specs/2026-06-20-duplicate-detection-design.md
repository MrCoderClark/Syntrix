# Section 19: Duplicate Detection — Design Spec

**Date:** 2026-06-20
**Branch:** `feat/duplicate-detection`
**Ships:** Similar-question suggestions during ask, mark-as-duplicate flow

## Overview

Help users find existing answers before posting a new question, and let
trusted community members link duplicates together. Two search strategies
(trigram for speed, tsvector for depth) work together across two touchpoints
(live typing, submit confirmation).

## Architecture Decisions

- **Similarity engine:** pg_trgm trigram similarity for live title matching,
  PostgreSQL tsvector full-text search for body-inclusive submit-time matching.
  Both are built-in — no external dependencies.
- **Scope:** Same community only. A question in c/golang doesn't surface
  results from c/sre.
- **Trigger:** Both live (while typing title) and submit-time (body-inclusive
  check before post creation).
- **Marking permissions:** Community mods/owners and users with 500+
  reputation.

## 1. Data Model

### New columns on `posts`

- `search_vector` (`tsvector`) — weighted full-text index. Title gets weight A,
  plain-text body gets weight B.
- `duplicate_of_id` (`UUID`, nullable, FK → `posts.id`) — self-referential.
  When set, this question is a duplicate of the referenced question.

### Indexes

- `GIN` index on `search_vector` for tsvector queries.
- `GIN` index on `title` using `gin_trgm_ops` for trigram similarity.

### Trigger

A PostgreSQL function `syntrix.posts_search_vector_update()` fires on INSERT
or UPDATE of `title` or `body_json`. It extracts plain text from `body_json`
by recursively walking the JSONB tree and concatenating all `text` values
from nodes with `"type": "text"` (same logic as `renderer.py`'s
`_extract_text`, but in PL/pgSQL). Then sets:

```sql
search_vector = setweight(to_tsvector('english', title), 'A')
             || setweight(to_tsvector('english', body_text), 'B')
```

### Backfill

The migration populates `search_vector` for all existing posts via a data
migration step. Post count is small enough for a single-pass UPDATE.

### No new tables

The duplicate relationship is a self-referential FK on `posts`. The
`search_vector` column lives on the same table to avoid join overhead.

## 2. Similarity Search API

Two endpoints, both community-scoped and question-only.

### Live title search

```
GET /api/communities/{slug}/questions/similar?title=...
```

- Uses `pg_trgm` `word_similarity()` against `posts.title`
- Filters: same community, `post_type='question'`, not deleted/removed
- Returns top 5 matches
- Minimum threshold: 0.3 similarity — below is filtered out

### Submit-time body check

```
POST /api/communities/{slug}/questions/similar
Body: { title: str, body_text: str }
```

- Builds a `tsquery` from title + body_text, ranks with `ts_rank_cd()`
  against `search_vector`
- Also runs trigram title match and merges results, deduplicating by post ID
- Returns top 5 matches, ranked by combined score
- Minimum threshold: 0.1 ts_rank

### Shared response shape

```json
{
  "id": "uuid",
  "title": "str",
  "score": 0,
  "answer_count": 0,
  "has_accepted_answer": false,
  "similarity": 0.75
}
```

## 3. Frontend UX

### Live suggestions (while typing title)

- Fires after 10+ characters typed and 300ms debounce pause
- Dropdown panel below the title input, up to 5 results
- Each result: title (linked, opens in new tab), vote count, answer count,
  green checkmark if accepted answer exists
- Only shown when `post_type='question'` is selected
- Dismisses on continued typing or click-away

### Submit interception

- After clicking submit, if the POST endpoint returns matches, show a
  confirmation modal before creating the post
- Modal: "Similar questions already exist" with the match list
- Two buttons: "Post anyway" (proceeds) and "Cancel" (returns to editor)
- If no matches, submit proceeds normally — no interruption
- The modal is a speed bump, not a blocker

### Duplicate banner

- Shown on question detail pages when `duplicate_of_id` is set
- Text: "This question has been marked as a duplicate of [Original Title]"
  with a link to the original
- Styled with `--accent-soft` background — informational, not punitive
- Question remains fully visible, answers still allowed

## 4. Mark-as-Duplicate Flow

### Permissions

- Community mods/owners: always
- Users with 500+ reputation: within communities they're members of
- Only `post_type='question'` posts can be marked
- Cannot mark as duplicate of itself
- Cannot mark as duplicate of another duplicate (no chains)

### API

```
POST /api/posts/{id}/mark-duplicate
Body: { duplicate_of_id: UUID }
```

Validates permissions, confirms both posts are in the same community, confirms
target isn't itself a duplicate. Sets `duplicate_of_id` on the question.

```
DELETE /api/posts/{id}/mark-duplicate
```

Unmarks the duplicate (same permission check).

### UI

- "Mark as duplicate" button on question detail pages for eligible users
- Clicking opens a search modal scoped to the same community's questions
- User searches for the original, selects it, confirms
- Duplicate banner appears immediately

### No penalties

No rep penalty for having a question marked as duplicate. No auto-close.
The question stays open and answerable — the duplicate link is a signpost.

## 5. Integration Points

### Backend

- `backend/app/models/post.py` — add `search_vector` (tsvector) and
  `duplicate_of_id` (UUID FK) columns
- `backend/app/posts/router.py` — add `duplicate_of_id` to response schemas,
  add mark/unmark endpoints
- New `backend/app/similarity/router.py` — the two similar-question endpoints
- New Alembic migration — columns, indexes, trigger function, backfill

### Frontend

- `frontend/app/(app)/c/[slug]/submit/page.tsx` — live suggestion panel below
  title input, submit interception modal
- `frontend/app/(app)/c/[slug]/post/[id]/page.tsx` — duplicate banner,
  mark-as-duplicate button + search modal

### Text extraction

The submit-time check needs plain text from TipTap JSON. The frontend uses
the editor's `.getText()` method — no new dependency.

### Dependencies

None. Both `pg_trgm` and tsvector are built into PostgreSQL. `pg_trgm` is
already enabled in the `syntrix` schema.

## Out of Scope

- Cross-community duplicate matching
- Auto-closing or locking duplicate questions
- Reputation penalties for duplicates
- ML/vector-based semantic similarity
- Duplicate detection for discussion posts (questions only)
- Suggestion UI in the TipTap editor body (title-only for live suggestions)
