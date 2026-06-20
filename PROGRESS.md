# Progress

Track build progress through Syntrix. Update this file as sections complete
(after merge to `main`). Claude reads this to understand where the project is.

## Current state — read this first

> **Phase 2 is in progress.** Tags, video embeds, Q&A post type,
> reputation + badges, and markdown polish are built.
>
> **Current branch:** `main`
> **Next action:** plan and build Section 19 (`feat/duplicate-detection`).

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

| # | Status | Branch | Ships |
|---|---|---|---|
| 14 | `[x]` | `feat/video-embed` | TipTap video embed node (YouTube, Vimeo, Twitch) |
| 15 | `[x]` | `feat/tags` | Community-scoped tags, CRUD, tag picker, tag pages |
| 16 | `[x]` | `feat/qa-posts` | Question post type, answers, voting, accept flow, feed filters |
| 17 | `[x]` | `feat/reputation` | Rep events, badges, awarding logic, profile display |
| 18 | `[x]` | `feat/markdown-polish` | Pygments code blocks, KaTeX math, Mermaid diagrams |
| 19 | `[ ]` | `feat/duplicate-detection` | Similar-question suggestions during ask, mark-as-duplicate |

## Phase 3 — Real-time Chat

*Not yet planned.*
