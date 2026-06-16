# Progress

Track build progress through Syntrix. Update this file as sections complete
(after merge to `main`). Claude reads this to understand where the project is.

## Current state — read this first

> **Phase 1 brainstorming is COMPLETE.** All design decisions are locked.
> The canonical spec is `PRD.md`; every visual decision is archived under
> `docs/superpowers/mockups/` as both HTML and retina PNG.
>
> **Next action:** invoke the `writing-plans` skill to produce
> `.agent/plans/1.scaffold.md` through `.agent/plans/10.voting-feeds.md`.
> Each plan is the detailed step-by-step for one feature branch.
>
> **After plans land and the user approves them:** implementation begins
> with branch `feat/scaffold` (section 01). The user owns every commit,
> push, and merge from that point on (see `CLAUDE.md` → "Branching & merge
> workflow — STRICT").
>
> No code has been written yet. No sections have started.

## Convention
- `[ ]` = Not started
- `[-]` = In progress (branch open)
- `[x]` = Completed (merged to `main`)

## Phase 1 — Foundation + Communities & Posts

| # | Status | Branch | Ships |
|---|---|---|---|
| 01 | `[-]` | `feat/scaffold` | Monorepo + `make dev` + pre-commit |
| 02 | `[ ]` | `feat/db` | `syntrix` schema, Alembic, extensions |
| 03 | `[ ]` | `feat/design-system` | Fonts, tokens, shell primitives |
| 04 | `[ ]` | `feat/auth` | OAuth, cookies, middleware, rate-limit table |
| 05 | `[ ]` | `feat/profiles` | `/u/<handle>`, profile edit (no avatar yet) |
| 06 | `[ ]` | `feat/communities` | List, landing, join/leave, request + admin approval |
| 07 | `[ ]` | `feat/storage` | `StorageBackend`, upload pipeline, avatars |
| 08 | `[ ]` | `feat/posts` | TipTap, post CRUD, image embeds, mod remove |
| 09 | `[ ]` | `feat/comments` | Threaded comments via `ltree`, mod remove |
| 10 | `[ ]` | `feat/voting-feeds` | Votes, triggers, Hot/New/Top feeds, home feed view |

Detailed per-section plans live in `.agent/plans/<n>.<slug>.md` and are written
by the writing-plans skill after the spec is approved.

## Phase 2 — Q&A Layer

*Not yet planned.*

## Phase 3 — Real-time Chat

*Not yet planned.*
