# Syntrix

![Syntrix](github-repo-image.png)

A community web app for gamers, IT admins, and developers — Reddit + Stack
Overflow + Discord under one identity.

See `PRD.md` for the spec, `CLAUDE.md` for working conventions, and
`PROGRESS.md` for status.

## Quick start

**Prerequisites:**
- Python 3.12, Node 22, GNU Make
- `uv` (`pipx install uv`) and `pre-commit` (`pipx install pre-commit`)
- A running local Supabase stack (Postgres + Storage via Docker)

**One-time setup:**

```bash
cp .env.example .env
# Edit .env — set PG_USER, PG_PASSWORD to match your Supabase pooler.
cd backend && uv sync && cd ..
cd frontend && npm install && cd ..
make precommit-install
```

**Database bootstrap** (requires a running Supabase Docker stack):

```bash
# Set role passwords then bootstrap the syntrix schema:
export SYNTRIX_ADMIN_PASSWORD=changeme
export SYNTRIX_APP_PASSWORD=changeme
make db-bootstrap

# Run migrations (DDL goes directly to the Postgres container):
make db-migrate
```

> DDL (schema/table changes) must run via `docker exec` because the Supavisor
> pooler does not persist session-level DDL. Reads and DML go through the
> pooler normally (port 6543).

**Day-to-day:**

```bash
make dev          # start backend (:8001) + frontend (:3000) in foreground
make test         # backend tests
make lint         # ruff + eslint + prettier check
make fmt          # auto-format everything
make db-current   # show current Alembic revision
make db-history   # show migration history
```

- Backend: http://127.0.0.1:8001 — FastAPI, hot-reload on file changes
- Frontend: http://127.0.0.1:3000 — Next.js, hot-reload on file changes

## Layout

- `backend/` — Python + FastAPI ("the brain")
- `frontend/` — Next.js + React + TypeScript
- `docs/superpowers/` — design artifacts (mockups, references)
- `.agent/plans/` — per-section implementation plans
