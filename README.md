# Syntrix

A community web app for gamers, IT admins, and developers. One identity, three
shapes of conversation: topic-scoped posts, structured Q&A, and live chat.

This repo is built collaboratively with Claude Code. The model writes the
code; the human directs, reviews, and lands every change. See
[`CLAUDE.md`](./CLAUDE.md) for the working conventions and the strict
branch-per-section workflow.

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Frontend | TBD — chosen with visual identity as a first-class requirement |

## Docs

- [`PRD.md`](./PRD.md) — what we're building, scope by phase, success criteria
- [`CLAUDE.md`](./CLAUDE.md) — Claude's working context: stack, rules, planning,
  branch workflow
- [`PROGRESS.md`](./PROGRESS.md) — section-by-section build progress
- [`.agent/plans/`](./.agent/plans/) — sequential implementation plans

## Phases

1. **Foundation + Communities & Posts** *(in design)*
2. **Q&A Layer** *(deferred)*
3. **Real-time Chat** *(deferred)*

## Getting Started (later)

A real getting-started section will land here once the stack is locked in and
the dev loop is reproducible.
