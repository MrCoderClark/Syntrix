---
description: Onboard Claude into the Syntrix codebase
---

# Onboard

## Process

1. **Read the bookmark first**
   - `PROGRESS.md` → "Current state" section at the top. This tells you
     exactly where the project is and what the next action is.
   - `CLAUDE.md` → "Start here — current state" at the top. Same purpose,
     from the Claude-conventions side.

2. **Scan structure**
   - Run `git ls-files` to see all tracked files
   - List `docs/superpowers/mockups/` to see the locked design artifacts

3. **Read the spec**
   - `PRD.md` (canonical Phase 1 spec — has TOC, architecture, data model,
     flows, permissions, section breakdown)
   - The most recent plan in `.agent/plans/`, if any exist yet
   - Any entry points / config touched in the last few commits

4. **Check state**
   - Run `git status` and `git log -10 --oneline`
   - Note the current branch — does it match an open section, or is it `main`?
   - Confirm `main` matches the last completed section per `PROGRESS.md`

## Output

A brief summary, in this exact order so the user can re-orient fast:

1. **Where we are** — the one-sentence "Current state" line. Are we in
   brainstorming, planning, or implementation? Which section?
2. **Next action** — what should happen next (e.g. "invoke writing-plans",
   "open `feat/auth` branch", "review plan `.agent/plans/3.design-system.md`").
3. **What Syntrix is** — one line.
4. **Tech stack** — one line.
5. **Repo structure** — one line.
6. **Current branch + recent activity** — last 3-5 commits.
7. **Open items / blockers** — anything that needs the user's attention.
