# Syntrix — PRD

> **Status:** Phase 1 design locked. Reviewed visually section by section
> via brainstorming companion (all artifacts in
> `docs/superpowers/mockups/`). Next step is `writing-plans` skill to
> produce per-section implementation plans in `.agent/plans/`.

## Table of Contents

1. What We're Building · Target Users · Anti-Goals
2. Scope by Phase
3. Stack
4. Visual Direction (+ Polish backlog)
5. Constraints
6. System Architecture
7. Data Model
8. Key Flows
9. Permissions & Rate Limits
10. Design Artifacts
11. **Phase 1 — Section Breakdown** ← the implementation roadmap
12. Success Criteria — Phase 1

---


## What We're Building

Syntrix is a community web app that brings together three patterns under one
identity:

1. **Communities & posts** (Reddit-style) — topic-scoped spaces, threaded
   comments, upvote / downvote, sortable feeds.
2. **Q&A** (Stack Overflow-style) — questions, accepted answers, tags,
   reputation, badges. *(Phase 2)*
3. **Real-time chat** (Discord-style) — public rooms scoped to communities,
   plus private invite-only rooms with DMs. *(Phase 3)*

It is **one product**, not three bolted together. The same identity, voice,
and UI shell hosts all three. A user signs up once and moves between
discussion, structured Q&A, and live chat without leaving the app.

## Target Users

Three overlapping audiences who today fragment across half a dozen tools:

- **Gamers** — currently scattered across Discord servers, subreddits, and
  game-specific forums.
- **IT admins** — homelabbers, sysadmins, MSP folks; today scattered between
  r/sysadmin, r/homelab, ad-hoc Discords, and Spiceworks.
- **Developers** — scattered between Stack Overflow, GitHub Discussions,
  language-specific Discords, and Reddit dev subs.

They share: technical fluency, a preference for substance over hype, and a
strong allergy to anything that looks generic or AI-templated.

## Anti-Goals

- Looking like a generic shadcn / Tailwind starter
- Becoming a generic "everything" social network
- Adding features whose only justification is "the competitor has it"
- Mobile-first compromises that make the desktop experience worse

## Scope by Phase

### Phase 1 — Foundation + Communities & Posts *(active)*

**In scope:**
- ✅ **OAuth-only auth** — GitHub, Google, Discord via `authlib`. JWT in httpOnly cookies. No password storage in Phase 1.
- ✅ User profiles (handle, display name, avatar, bio, audience tag)
- ✅ Communities — **admin-curated** (only platform admins create them in Phase 1; users submit requests via a form). Owners can rename, *not* delete. Mod powers: remove post/comment, pin one post, ban user. No automod/audit-log-UI in Phase 1. Private communities deferred to Phase 3.
- ✅ Posts — **TipTap rich-text editor** as primary UX, with markdown as a first-class alternate (paste markdown auto-converts; "view as markdown" source toggle for power users). Code blocks with real syntax highlighting via Shiki. **Native image uploads** to S3-compatible bucket (recommendation: Cloudflare R2). Title required (≤200 chars), body optional, max 40k chars. Link-only posts allowed with auto-fetched OG preview.
- ✅ Threaded comments
- ✅ Upvote / downvote with score
- ✅ Sorted feeds (Hot / New / Top)
- ✅ Visual identity & design system
- ✅ Account settings page

**Out of scope (deferred to later phases):**
- ❌ Q&A post type / accepted answers / reputation
- ❌ Real-time chat
- ❌ Direct messages
- ❌ Notifications system (a minimal indicator may exist, no system yet)
- ❌ Mobile apps
- ❌ Search beyond basic community/post filtering

### Phase 2 — Q&A Layer *(deferred)*

Question / answer post type, accepted answer, tags + tag pages,
reputation + badges, markdown polish (code highlighting, math, diagrams),
duplicate detection, "answer-shaped" feeds.

### Phase 3 — Real-time Chat *(deferred)*

WebSocket gateway, public rooms scoped to communities, private rooms with
invites, presence + typing indicators, message history + search, DMs.

## Stack

| Layer | Choice |
|-------|--------|
| Backend | Python + FastAPI |
| Database | PostgreSQL — **reused from local Supabase Docker stack**, isolated in the `syntrix` schema. Dedicated `syntrix_app` role with grants scoped to that schema only. Connection via Supavisor pooler at `127.0.0.1:5432`. |
| Frontend framework | **Next.js (App Router, React, TypeScript)** |
| Styling | Hand-rolled CSS + CSS variables (no Tailwind utility-flood; component-scoped styles) |
| Typography | Fraunces (display, variable serif w/ SOFT axis) + Hanken Grotesk (body) + JetBrains Mono (meta / code) |
| Auth | **FastAPI-owned**: bcrypt-free (OAuth-only), JWT in httpOnly cookies, providers via `authlib` |
| OAuth providers (Phase 1) | GitHub, Google, Discord |
| Authz pattern | Defense in depth: Next.js middleware verifies JWT (auth only, no perm logic). FastAPI re-verifies JWT + enforces resource authz (ownership, mod role, ban, membership). |
| Image durability | Direct browser → Supabase Storage via signed PUT URL (5 min TTL); FastAPI finalize validates + EXIF-strips + moves to permanent path; `post_attachments` table links to post. Images permanent until: post delete (cascade), edit removes from TipTap doc (orphan reconciliation), or `tmp/` 24h TTL sweep. |
| Post editor | **TipTap** (React) with custom code-block (Shiki), image, link-preview, table extensions. Canonical storage = TipTap JSON. Server renders to HTML for SSR + cached. |
| Object storage | **Supabase Storage** (reusing the running `storage` container from the user's local Supabase stack). Bucket: `syntrix-uploads`. Signed-URL upload flow from FastAPI. EXIF stripped, dimensions+content-type validated server-side. Max 8 MB per image; JPG/PNG/WEBP/GIF only (no SVG). Wrapped behind a `StorageBackend` interface so the app remains portable to S3/R2/etc. without code rewrites. |
| Realtime (Phase 3) | TBD |
| Hosting (dev) | **All local** via Docker Compose — Syntrix's `docker-compose.yml` compose-extends the existing Supabase stack (Postgres, Storage) and adds FastAPI + Next.js containers. Single `make dev` brings up the full loop. |
| Hosting (production) | **Deferred** — decided after Phase 1 implementation lands. Code should be deployment-agnostic (12-factor: config from env, no hardcoded paths, stateless backends). |
| Observability | Phase 1: Python `logging` (structured JSON via `structlog`) + FastAPI request logs. Frontend: console only. No external service. |

The TBD items are decided during the Phase 1 design conversation and pinned
back into this PRD and `CLAUDE.md` once locked in.

## Visual Direction *(locked)*

**Reference:** `docs/superpowers/references/segment-community-reference.png`
adapted for Syntrix's voice.
**Mockup:** `docs/superpowers/mockups/phase1-home.{html,png}`
**Direction:** Editorial-Refined with Atmospheric Texture.

**Core decisions:**

- **Background:** warm paper (`#f6f3ec`), never cold white. Sitewide subtle SVG
  noise overlay (`multiply` blend, ~0.35 opacity) for warmth.
- **Accent:** persimmon (`#e8472b`) — not blue, not purple. Used sparingly
  (wordmark dot, hot tab underline, primary button hover).
- **Wordmark:** "Syntrix." in Fraunces Bold Italic with `SOFT` axis at 80,
  persimmon dot. The dot is identity.
- **Per-community color signature:** every community has its own color
  (`--c-homelab`, `--c-halo`, etc.) that flows through its post-card art.
  Six anchored: homelab=navy, halo=crimson, sre=plum, proxmox=olive,
  golang=teal, security=oxblood. New communities pick from a curated palette.
- **Post-card art:** SVG-generated, never image files. Each card uses its
  community color + 2-3 radial/linear gradients + an SVG noise overlay for grain.
- **Typography hierarchy:**
  - Display: Fraunces (italic accents on key words — "Your *feed*", etc.)
  - Body: Hanken Grotesk 500/600
  - Meta: JetBrains Mono (uppercase labels, scores, timestamps)
- **Motion:** staggered fade+rise on initial page-load (50ms increments). No
  hover micro-animations beyond a 2px lift + shadow.
- **No rounded corners larger than 14px.** No glassmorphism. No purple
  gradients on white. No Inter, Geist, or Space Grotesk.

### Polish backlog *(Phase 1 section work)*

These were noted during v1 review and roll into the Phase 1 plan as
section-scoped polish:

1. **Card art needs geometric form** — current art is just radial gradient
   blobs. Add per-community geometric motifs (stripes, orbits, dots, grid)
   layered inside the gradient. *(Highest impact.)*
2. **Visual hierarchy on the feed** — pinned / top post should get a
   2-column-wide treatment to anchor the eye.
3. **Post-type signals** — small icon ribbon indicating text / link / image /
   code-heavy post.
4. **Replace the placeholder "S" page-header glyph** with a real Syntrix mark.
5. **Earned ribbons beyond ★ pinned** — "trending," "from someone you follow,"
   "first reply in 2h."
6. **Empty / loading / error states** and **mobile responsive** and
   **accessibility (focus rings, ARIA, keyboard nav)** all designed per-section.

## Constraints

- Backend is **Python** (non-negotiable — the "brain")
- Frontend is "any modern stack" — but must be chosen with the visual-identity
  requirement in mind (i.e. not chosen for the convenience of stock components)
- No looking AI-generated. Reviewed per section.
- Branch-per-section workflow (see `CLAUDE.md`)

## System Architecture

**Mockup:** `docs/superpowers/mockups/phase1-architecture.{html,png}`

Five components, two trust boundaries:

- **Browser** — React (client) holding the session cookie. Drag-and-drops
  images directly to object storage; never tunnels binaries through the API.
- **Next.js** — SSR + App Router + TypeScript. Holds **zero business logic**.
  Every meaningful action is a fetch to FastAPI. Middleware verifies the JWT
  signature + expiration before any protected route renders.
- **FastAPI ("the brain")** — owns identity (OAuth dance + JWT issuance),
  data access (SQLAlchemy 2.0 async + Alembic), all authorization,
  TipTap → HTML rendering (cached), and upload coordination (signing,
  validation, EXIF stripping, lifecycle).
- **Postgres** — the user's local Supabase database, isolated to the
  `syntrix` schema. Single source of truth: users, communities, posts,
  comments, votes, refresh tokens, mod actions.
- **Supabase Storage** — the user's local Supabase storage container.
  Browser uploads directly via signed PUT URLs; FastAPI validates and moves
  bytes between `tmp/` → `pending/` → `posts/<post-id>/<sha>.ext`.

**Trust boundaries:**
- **Authn at the edge** (Next.js middleware) for fast rejection of unauth
  requests. **Authz only in FastAPI** — single source of truth for every
  "are they allowed to" question.
- **OAuth provider access tokens are never persisted** — discarded after the
  callback once we have `(provider, sub, email)`.

**What's deliberately not in Phase 1:** Redis (FastAPI in-process cache is
enough), Celery / background workers (the 24 h tmp/ sweep is a cron task,
not a worker), CDN (deferred with production hosting), analytics service
(structured logs only).

## Data Model

**Mockup:** `docs/superpowers/mockups/phase1-data-model.{html,png}`

12 domain tables in 4 bands, plus one infrastructure table
(`rate_limit_buckets`, owned by Section 04). All in the `syntrix` schema.
Postgres only — no NoSQL, no Elasticsearch, no Redis.

| Band | Tables |
|---|---|
| Identity | `users`, `oauth_identities`, `refresh_tokens` |
| Structure | `communities`, `community_memberships`, `community_requests` |
| Content | `posts`, `post_attachments`, `comments` |
| Engagement | `post_votes`, `comment_votes`, `mod_actions` |

**The non-obvious choices:**

1. **TipTap JSON in `jsonb`** — canonical form. Server pre-renders to a
   `body_html` cached column on every create/edit; read paths never re-render.
2. **Soft delete posts/comments** (`deleted_at`), hard delete attachments
   (`ON DELETE CASCADE` + async storage sweep). Preserves audit graph
   integrity; keeps storage bounded.
3. **Author delete ≠ mod removal** — separate columns (`deleted_at` vs.
   `removed_at + removed_by`). UI distinguishes "[deleted by author]" from
   "[removed by mod for: spam]".
4. **Triggers maintain counters** — `posts.score`, `posts.comment_count`,
   `comments.score`. Atomic with the vote/comment insert; no app math.
5. **Two vote tables, not polymorphic** — keeps real foreign keys.
   `post_votes` and `comment_votes` separately.
6. **No sessions table** — `refresh_tokens` *are* the session. "Log out
   everywhere" = `UPDATE refresh_tokens SET revoked_at = now() WHERE user_id = $1`.
7. **Postgres extensions:** `citext` (case-insensitive handles + slugs),
   `pg_trgm` (fuzzy search later), `ltree` (comment tree subtree fetch),
   `pgcrypto` (`gen_random_uuid()`).

**Explicitly out of scope (Phase 1):** notifications table, tags, follow
graph, DMs, mod-action UI.

**Key indexes:**
- `posts (community_id, created_at desc)` — community "New" feed
- `posts ((computed_hot_score) desc)` — global "Hot" via functional index
- `comments (post_id, path)` — `ltree` subtree fetch
- `oauth_identities (provider, provider_sub)` unique — login lookup
- `refresh_tokens (user_id) where revoked_at is null` — partial, active sessions

## Key Flows

**Mockup:** `docs/superpowers/mockups/phase1-flows.{html,png}`

Four representative flows that exercise every interesting edge:

### Flow 1 — OAuth signin

1. Browser → Next.js: "Sign in with GitHub."
2. Next.js → 302 → FastAPI `/api/auth/login/github`.
3. FastAPI mints an HMAC-signed `state` cookie, 302s to GitHub's
   authorize URL.
4. User authorizes → GitHub 302s back to `/api/auth/callback/github`.
5. FastAPI exchanges `code` for access token, fetches `/user`,
   **discards the access token**, UPSERTs `oauth_identities + users` by
   `(provider, sub)`.
6. FastAPI sets `access` (15 min) + `refresh` (30 d, hashed in DB) httpOnly
   cookies; 302s to home.

**Load-bearing:** `state` is HMAC-signed and round-trips, catching CSRF.
UPSERT key is `(provider, sub)` not email (emails change, sub doesn't).
Different-provider email collision surfaces "link existing account?" — never
silent merge.

### Flow 2 — Create a post with an image *(the hard one)*

**Band A — upload (image exists before the post does):**
1. Browser → FastAPI `POST /uploads/sign {filename, mime}` →
   `{key=tmp/<rand>.jpg, url, expires_in=300}`.
2. Browser → Supabase Storage: direct PUT to the signed URL.
3. Browser → FastAPI `POST /uploads/finalize {key}` →
   FastAPI reads, validates mime, strips EXIF, computes sha + dimensions,
   COPYs `tmp/` → `pending/`, returns canonical URL.
4. TipTap embeds the URL as an image node.

**Band B — submit (image becomes permanent):**
5. Browser → FastAPI `POST /posts {community_id, title, body_json}`.
6. FastAPI: authz (member ∧ ¬banned), parse `body_json`, extract image URLs,
   INSERT post + INSERT `post_attachments`, then COPY `pending/` →
   `posts/<post-id>/<sha>.jpg` and DELETE pending. **DB writes happen
   first**; storage mutations follow. If the transaction rolls back, bytes
   stay in `pending/` and get swept normally.

### Flow 3 — Vote

1. Browser → FastAPI `POST /posts/<id>/vote {value: 1}`.
2. FastAPI: authz (logged in, not banned, not own content).
3. SQL: `INSERT INTO post_votes ... ON CONFLICT (user_id, post_id)
   DO UPDATE SET value = EXCLUDED.value`.
4. Postgres trigger `after_post_vote_change` recomputes `posts.score`
   atomically.
5. FastAPI returns `{score, user_vote}`; UI confirms the optimistic update.

### Flow 4 — Comment

1. Browser → FastAPI `POST /posts/<id>/comments {body_json, parent_comment_id?}`.
2. FastAPI: authz (member, not banned). Render TipTap JSON → HTML
   server-side. Compute `depth + path` (ltree) from parent.
3. INSERT into `comments`. Trigger increments `posts.comment_count`.
4. Response includes rendered HTML; UI inserts at the correct tree depth.

**Things every flow shares:**

- **Auth at the edge first** — Next.js middleware rejects unauth requests
  before they cost backend time.
- **FastAPI re-verifies the JWT** — never trust the edge.
- **Resource authz is its own dependency** — `Depends(current_user)` then
  `Depends(can(action, resource))`. The "can" helper hits cached membership
  state, one round-trip max.
- **Writes use serializable transactions.** Triggers run inside the write
  txn so counters can't desync.
- **Uniform error envelope** — `{error: {code, message, details?}}` with a
  stable `code` the frontend dispatches on.

## Permissions & Rate Limits

**Mockup:** `docs/superpowers/mockups/phase1-permissions.{html,png}`

**Five roles:** Anonymous → Member → Mod → Owner → Admin.

**Matrix overview** (full grid in the mockup):
- **Anonymous:** can browse public communities, posts, comments, profiles.
  Cannot vote, post, comment, join.
- **Member:** can post / comment / vote in any community they've joined and
  aren't banned from. Can edit / delete own content. **Cannot vote on own
  content** (anti-gaming).
- **Mod:** member powers + remove post, remove comment, pin one post **per
  community** (pinning a new one auto-unpins the previous), ban user from
  their community. *Cannot* edit other users' content (that would lie about
  authorship).
- **Owner:** mod powers + rename, edit description, change community color,
  appoint/demote mods. Cannot delete community (admin-only).
- **Admin:** everything. Creates communities by approving requests.
  Suspends users platform-wide.

**Authz implementation:**
- One function per action in `backend/app/auth/perm.py`
  (`can_create_post(user, community)`, `can_remove_post(user, post)`, etc.).
- Used as a FastAPI dependency:
  `Depends(can("create_post", community_id))` → raises 403 on deny.
- No `if user.is_admin` sprinkled through handlers. `perm.py` is the only
  place that knows.
- Membership + role + ban queried once per request, cached.

**HTTP semantics:**
- `403` — caller exists but isn't allowed.
- `404` — resource exists but caller may not know it exists. (Rare in
  Phase 1 — public communities don't hide.)
- `429` — rate-limited. Returns `Retry-After` header + next-refill timestamp.

**Rate limits** (Phase 1 — in Postgres, no Redis):

| Surface | Limit | Scope | Algorithm |
|---|---|---|---|
| Create post | 10 / hr · 50 / day | per user | token bucket |
| Create post (first 24 h of account) | 3 / hr · 10 / day | per user | token bucket |
| Create comment | 60 / hr · 300 / day | per user | token bucket |
| Vote | 600 / hr | per user | token bucket |
| Request signed upload URL | 100 / hr | per user | token bucket |
| Login attempt | 10 / 15 min | per IP | sliding window |
| Login attempt | 5 / 15 min | per account | sliding window |
| OAuth callback | 30 / 15 min | per IP | sliding window |
| Community request | 2 / day | per user | fixed window |
| Generic API catch-all | 300 / min | per IP | leaky bucket |

One table: `rate_limit_buckets(key, tokens, refilled_at)`. Atomic refill+take
in a single `UPDATE … RETURNING` with a `WHERE tokens >= cost` guard. Returns
0 rows → 429. Janitor sweeps stale rows nightly.

**Deliberately out of scope (Phase 1):** report/flag flow (Phase 2),
audit-log admin UI (rows written, no view), automod / regex bans / link
blacklists (Phase 2+), captcha (rate limits + OAuth-only gating cover most
spam vectors).

## Design Artifacts

Every design decision is captured as both HTML (for iteration) and a retina
PNG (for permanent reference) under `docs/superpowers/mockups/`:

| Artifact | Mockup files |
|---|---|
| Home / feed visual identity | `phase1-home.{html,png}` |
| System architecture | `phase1-architecture.{html,png}` |
| Data model (ER diagram + non-obvious choices) | `phase1-data-model.{html,png}` |
| Key flows (sequence diagrams) | `phase1-flows.{html,png}` |
| Permissions matrix + rate limits | `phase1-permissions.{html,png}` |
| 10-section implementation breakdown | `phase1-section-plan.{html,png}` |

Per `CLAUDE.md` → "Mockup archiving — STRICT", every new or updated visual is
re-synced to this directory automatically (HTML copy + Playwright-rendered
2× full-page PNG). The brainstorming companion files in
`.superpowers/brainstorm/` are gitignored and ephemeral; this directory is
the permanent record.

## Phase 1 — Section Breakdown

Phase 1 is decomposed into **10 sections**, each a single feature branch in the
strict branch-per-section workflow. Dependencies flow downward — no section
begins before its prerequisites have been merged to `main`. Each section's
detailed implementation plan lives in `.agent/plans/<n>.<slug>.md` after the
spec is approved.

| # | Branch | Type | Ships | Depends on |
|---|---|---|---|---|
| 01 | `feat/scaffold` | infra | Monorepo skeleton (`backend/` + `frontend/`), `docker-compose.yml` compose-extending the existing Supabase stack, `make dev` loop, pre-commit hooks | — |
| 02 | `feat/db` | backend | `syntrix` schema isolation, `syntrix_app` role, Alembic with `include_object` filter, SQLAlchemy 2.0 async, extensions (`citext`, `pg_trgm`, `ltree`, `pgcrypto`), test fixtures | 01 |
| 03 | `feat/design-system` | frontend | Fonts via `next/font` (Fraunces / Hanken Grotesk / JetBrains Mono), CSS variable tokens, shell primitives (Sidebar, Topbar, Button, IconButton, Avatar, Tab, Input, PageHeader, Card), paper bg + noise overlay, wordmark, 404 + loading states | 01 |
| 04 | `feat/auth` | full-stack | OAuth (GitHub / Google / Discord), JWT in httpOnly cookies, `current_user` dep, Next.js middleware, `/signin` page, `perm.py` skeleton, `rate_limit_buckets` table + helper (first surface to land it) | 02, 03 |
| 05 | `feat/profiles` | full-stack | `/u/<handle>` public profile, `/settings/profile` edit (display name, bio, audience tag — no avatar yet) | 04 |
| 06 | `feat/communities` | full-stack | `/communities` list, `/c/<slug>` landing with per-community color signature, join/leave, community-request form, admin approval UI | 04 |
| 07 | `feat/storage` | full-stack | `StorageBackend` interface + `SupabaseStorageBackend`, `/uploads/sign` + `/uploads/finalize`, EXIF strip + mime validation + dimensions, `tmp/` orphan sweep, avatar upload integrates back into profiles | 04 |
| 08 | `feat/posts` | full-stack | TipTap editor (code-block via Shiki, image, link-preview, table), markdown source-toggle, post CRUD, OG link previews, post detail page, mod remove. **May split** into `feat/posts-core` + `feat/posts-editor` at writing-plans time if scope grows. | 06, 07 |
| 09 | `feat/comments` | full-stack | Threaded comments (TipTap), `ltree` subtree fetch, reply UI, author delete + mod remove | 08 |
| 10 | `feat/voting-feeds` | full-stack | Upvote/downvote (posts + comments), Postgres triggers maintain counters, Hot / New / Top feed algorithms, "Your feed" home view | 08, 09 |

**Cross-cutting:** `app/auth/perm.py` and the `rate_limit_buckets` table land in Section 04 and each subsequent section adds its own permission functions and rate-limit keys. There is no standalone "permissions section" or "rate-limits section."

**Estimated wall time:** ~18 working days of build (you in the loop reviewing and merging each PR). Real-world ~3–4 weeks of evenings/weekends.

**Polish backlog** (from §Polish backlog above) lands alongside the relevant section — not deferred to a separate cycle.

## Success Criteria — Phase 1

By the end of Phase 1, the project should:

- ✅ Allow a new visitor to sign up, create / join a community, post, comment,
  and vote.
- ✅ Have a distinct, deliberate visual identity that does **not** read as
  "AI-generated SaaS starter".
- ✅ Be built on a backend whose data model can absorb Phase 2 (Q&A) and Phase
  3 (chat) without a rewrite.
- ✅ Have automated tests covering auth, post/comment CRUD, voting, and feed
  sorting.
- ✅ Run locally with one `make dev` (or equivalent) command.
