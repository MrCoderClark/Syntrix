# Section 20: Phase 2 Polish — Design Spec

**Date:** 2026-06-22
**Branch:** `fix/phase2-polish`
**Ships:** Error handling, vote state persistence, search/feed integration, UX polish

## Overview

QA sweep across Phase 2 features (sections 14–19) fixing error handling gaps,
missing loading states, integration seams between Phase 2 and Phase 1, and
minor UX rough edges. No new features — only fixes and integration work.

## 1. Vote State Persistence

Every `VoteWidget` in the app is initialized with `userVote={0}`, so users
never see their existing votes highlighted after a page load.

### Backend

New batch endpoint:

```
GET /api/votes/mine?target_type=post&target_ids=id1,id2,...
```

- Requires auth (`CurrentUser`). Returns `{}` for unauthenticated users.
- `target_type`: one of `post`, `comment`, `answer`.
- `target_ids`: comma-separated UUIDs, max 50.
- Response: `{ "votes": { "<id>": <value>, ... } }` — only IDs with
  non-zero votes are included.
- Single query: `SELECT target_id, value FROM votes WHERE user_id = :uid
  AND target_type = :type AND target_id IN (:ids)`.

### Frontend

Each page that renders VoteWidgets fetches the user's votes once on mount:

- **Post detail page** (`page.tsx`): fetch votes for the post ID, then pass
  `userVote` to the post's VoteWidget. The page is a server component, so
  the fetch happens server-side with the user's cookie forwarded.
- **AnswerSection**: fetch votes for all answer IDs in one call, pass
  `userVote` to each AnswerCard.
- **CommentSection**: fetch votes for all visible comment IDs, pass
  `userVote` to each CommentNode.
- **CommunityFeed / HomePage**: fetch votes for all visible post IDs, pass
  `userVote` to each VoteWidget. These are client components, so the fetch
  happens client-side after mount.

The `VoteWidget` component itself doesn't change — callers pass the correct
initial value instead of hardcoded `0`.

## 2. Search & Feed Integration

### Search — add tag awareness

The `/api/search` endpoint currently only searches posts by title (`ILIKE`).

**Add tag results:** Join `QuestionTag` + `Tag` tables. Posts that have a
matching tag should appear in post results even if their title doesn't match.
Also add a `tags` section to `SearchResponse`:

```json
{
  "posts": [...],
  "communities": [...],
  "users": [...],
  "tags": [
    { "id": "...", "slug": "python", "name": "Python", "color": "#3572A5", "community_slug": "dev", "usage_count": 42 }
  ]
}
```

Tag search: `Tag.name ILIKE pattern OR Tag.slug ILIKE pattern`, scoped to
non-deleted communities. Max 5 tag results.

### Feeds — load tags for question posts

The community feed (`/api/communities/{slug}/posts`) and home feed
(`/api/feeds/home`) return posts without tag data. Questions in feeds should
include their tags.

**Approach:** After fetching the page of posts, batch-load tags for all
question-type posts in one query:

```sql
SELECT qt.question_id, t.id, t.slug, t.name, t.color
FROM question_tags qt JOIN tags t ON qt.tag_id = t.id
WHERE qt.question_id IN (:post_ids)
```

Attach tags to each `PostResponse`. Frontend feed components conditionally
render `TagPill` for question posts that have tags.

## 3. Error Handling & Loading States

Six targeted fixes in existing components.

### AnswerCard.handleSaveEdit — error feedback

Currently silently fails when the PATCH returns an error. Add an `editError`
state variable. On non-ok response, parse the error detail and display it
below the editor. Clear on next save attempt.

### AnswerCard.handleDelete — confirmation dialog

Add `window.confirm("Delete this answer? This cannot be undone.")` before
the DELETE fetch, matching the existing pattern in `PostActions.handleDelete`.

### PostActions.handleUnmarkDuplicate — error check + loading state

- Check `res.ok` before calling `router.refresh()`.
- Add `unmarking` state boolean. Set `true` before fetch, `false` after.
- Button shows "Unmarking..." and is `disabled` while in flight.

### accept_answer backend — idempotency guard

If `answer.is_accepted` is already `True`, return `{"status": "accepted"}`
immediately without re-awarding reputation. Same pattern: if `unaccept` is
called on a non-accepted answer, it already returns 400.

### Modal Escape key dismissal

Both modals (submit interception in `submit/page.tsx` and mark-as-duplicate
in `PostActions.tsx`) need a `useEffect` with a `keydown` listener that
closes the modal on Escape:

```tsx
useEffect(() => {
  if (!showModal) return;
  const handler = (e: KeyboardEvent) => {
    if (e.key === "Escape") setShowModal(false);
  };
  document.addEventListener("keydown", handler);
  return () => document.removeEventListener("keydown", handler);
}, [showModal]);
```

## 4. Minor UX Polish

### Shared SimilarQuestion type

Extract the `SimilarQuestion` interface (duplicated in `submit/page.tsx` and
`PostActions.tsx`) to `frontend/types/similarity.ts`. Import from both files.

### Inline style → CSS class

Replace the inline `style={{ color: "var(--ink-faint)" }}` on the empty-state
label in `PostActions.tsx` with a `.dupResultEmpty` class in
`PostDetail.module.css`.

### Empty suggestions feedback

In the submit page, when the user types 10+ characters but the similarity
search returns zero results, show a "No similar questions found" message in
the suggestions panel instead of hiding it entirely. Helps the user know the
search ran and found nothing.

## Out of Scope

- Permission-gated visibility for mark-as-duplicate buttons (consistent with
  existing Edit/Delete/Mod-remove pattern — backend enforces, frontend shows
  to all)
- `duplicate_of_title` in list/feed responses (not needed in feeds)
- Focus trapping in modals (would require a focus-trap library or significant
  custom code — out of scope for a polish pass)
- Notification system
- Mobile-specific responsive fixes (separate section if needed)
