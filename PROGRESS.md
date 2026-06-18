# Progress

Track build progress through Syntrix. Update this file as sections complete
(after merge to `main`). Claude reads this to understand where the project is.

## Current state — read this first

> **Phase 1 is feature-complete + polished.** All 10 core sections plus
> polish, user menu/search, and enhanced profiles merged to `main`.
>
> **Current branch:** `main`
> **Next action:** decide what's next — Phase 2 planning, or additional
> Phase 1 enhancements.

## Convention
- `[ ]` = Not started
- `[-]` = In progress (branch open)
- `[x]` = Completed (merged to `main`)

## Phase 1 — Foundation + Communities & Posts

| # | Status | Branch | Ships |
|---|---|---|---|
| 01 | `[x]` | `feat/scaffold` | Monorepo + `make dev` + pre-commit |
| 02 | `[x]` | `feat/db` | `syntrix` schema, Alembic, extensions |
| 03 | `[x]` | `feat/design-system` | Fonts, tokens, shell primitives |
| 04 | `[x]` | `feat/auth` | OAuth, cookies, middleware, rate-limit table |
| 05 | `[x]` | `feat/profiles` | `/u/<handle>`, profile edit (no avatar yet) |
| 06 | `[x]` | `feat/communities` | List, landing, join/leave, request + admin approval |
| 07 | `[x]` | `feat/storage` | `StorageBackend`, upload pipeline, avatars |
| 08 | `[x]` | `feat/posts` | TipTap, post CRUD, image embeds, mod remove |
| 09 | `[x]` | `feat/comments` | Threaded comments via `ltree`, mod remove |
| 10 | `[x]` | `feat/voting-feeds` | Votes, triggers, Hot/New/Top feeds, home feed view |
| 11 | `[x]` | `fix/phase1-polish` | QA pass, responsive, loading states, error handling |
| 12 | `[x]` | `feat/user-menu-search` | Avatar dropdown menu, site-wide search |
| 13 | `[x]` | `feat/profiles-v2` | Stats, social links, activity tabs, enriched profile |

Detailed per-section plans live in `.agent/plans/<n>.<slug>.md` and are written
by the writing-plans skill after the spec is approved.

## Phase 2 — Q&A Layer

*Not yet planned.*

## Phase 3 — Real-time Chat

*Not yet planned.*
