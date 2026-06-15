---
description: Build from a plan in .agent/plans/, respecting the branch workflow
argument-hint: [path-to-plan]
---

# Build

Read and execute: `$ARGUMENTS`

## Process

1. **Confirm branch state** — before touching anything, verify:
   - `main` contains the prior section's merge (`git fetch && git status`)
   - You are on (or are about to create) the correct section branch
   - No prior section branch is still unmerged
   If any of those fail, stop and surface the problem.

2. **Read the entire plan** — understand all tasks, dependencies, validation
   steps, and the section boundary.

3. **Execute tasks in order** — follow project conventions in `CLAUDE.md`.
   Verify syntax and imports after each change. Keep the diff focused on the
   plan's section — no drive-by refactors.

4. **Run validation** — execute the plan's tests / checks. For UI work,
   exercise the feature in a real browser. Fix issues before proceeding.

5. **Stop at the section boundary** — when the section is complete, **do not
   create the next branch**. Hand back to the user with:
   - Summary of tasks completed
   - Files created / modified
   - Test results
   - Any deviations from the plan and why
   - Suggested commit message

The user takes it from there: commit, push, PR, merge, delete branch. Only
after they confirm the merge does the next section start.
