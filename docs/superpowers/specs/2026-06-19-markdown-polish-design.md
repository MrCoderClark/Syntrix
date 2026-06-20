# Section 18: Markdown Polish — Design Spec

**Date:** 2026-06-19
**Branch:** `feat/markdown-polish`
**Ships:** Shiki-quality code highlighting, KaTeX math rendering, Mermaid diagrams

## Overview

Upgrade the post/answer/comment rendering pipeline with three features:
syntax-highlighted code blocks, LaTeX math, and Mermaid diagrams. The goal
is a reading experience on par with GitHub and Stack Overflow for a developer
audience.

## Architecture Decision

**Hybrid: server-side Pygments + KaTeX, client-side Mermaid.**

- Code highlighting and math render at write time in `renderer.py` — readers
  get instant, zero-JS output.
- Mermaid renders client-side via dynamic import — avoids a Puppeteer/Chromium
  dependency on the backend.

## 1. Code Highlighting — Pygments (server-side)

### Write path

`renderer.py`'s `codeBlock` handler calls Pygments instead of emitting raw
`<pre><code class="language-X">`. The `attrs.language` from TipTap JSON maps
to a Pygments lexer.

Output: `<pre class="highlight"><code>` with Pygments token spans
(`<span class="k">`, `<span class="s">`, etc.).

### Theme

A single dark CSS theme (One Dark family) matching the existing
`var(--ink)` code block background. Token colors defined in a
`pygments-theme.css` file loaded globally.

### Editor

Keeps lowlight/highlight.js as-is for live editing. Colors won't be
pixel-identical between editor and rendered output but will be close.

### Fallback

Unrecognized language tags fall back to plain text — no error, no crash.

### Dependencies

- `pygments` (PyPI) added to `pyproject.toml`

## 2. Math Rendering — KaTeX (server-side)

### Parsing

`renderer.py` scans text nodes for LaTeX delimiters *before* HTML-escaping:

- `$$...$$` → block math (matched first, greedy) → wrapped in
  `<div class="math-block">`, rendered with `displayMode: true`
- `$...$` → inline math → rendered with `displayMode: false`
- `\$` → literal dollar sign (escaped, not parsed)

### Rendering

A small Node helper script (`scripts/render-katex.mjs`) that imports the
`katex` npm package and reads LaTeX strings from stdin (JSON array), returns
rendered HTML fragments. Called via subprocess from `renderer.py`. Node is
already available on the system for Next.js.

The script is batch-oriented — `renderer.py` collects all math expressions
in a document, calls the script once, and splices the results back in.
Avoids per-expression subprocess overhead.

### Fonts

KaTeX needs its font files (KaTeX_Main, KaTeX_Math, etc.). Served as static
assets from `public/fonts/katex/` with a small CSS file for `@font-face`
declarations.

### Error handling

If KaTeX can't parse the LaTeX, the raw source is rendered in
`<code class="math-error">` with a red-tinted background so the author sees
something went wrong.

### Editor experience

`$...$` appears as raw text while editing. No live preview — the author sees
rendered math after publishing. Keeps the editor simple.

### Dependencies

- `katex` (npm) added to a top-level `scripts/package.json` (separate from
  the frontend — backend helper scripts)
- KaTeX font files + CSS in `public/fonts/katex/`

## 3. Mermaid Diagrams (client-side)

### Storage

`renderer.py` treats `mermaid` code blocks like any other — Pygments won't
recognize the language, so the block passes through as plain text in
`<pre><code class="language-mermaid">`. Raw Mermaid source is preserved in
`body_html`.

### Client rendering

A `<MermaidBlock>` React component. A wrapper around the post content
container finds all `<pre><code class="language-mermaid">` elements after
mount, extracts the text, and calls `mermaid.render()` to produce SVG that
replaces the `<pre>` block.

### Lazy loading

Mermaid JS (~300KB) is dynamically imported — `import("mermaid")` — only
when the page contains a `language-mermaid` block. Zero cost if no diagrams.

### Theme

Mermaid configured with a custom theme that picks up Syntrix's CSS variables
(`--ink`, `--paper`, `--accent`) so diagrams feel native.

### Fallback

While loading or on render failure, the raw Mermaid source stays visible in
the `<pre>` block (readable as plain text). On failure, a subtle error
banner appears above the block.

### Scope

Only on content display pages (post detail, answer cards, comment nodes).
Not on feed cards.

### Dependencies

- `mermaid` (npm) added to `package.json`

## 4. Integration Points

### Backend

- `renderer.py` — Pygments code highlighting + KaTeX math parsing in text
  nodes. No new TipTap node types; both work within the existing JSON
  structure.
- `pyproject.toml` — add `pygments`

### Scripts

- `scripts/render-katex.mjs` — Node helper called by `renderer.py` via
  subprocess. Batch renders LaTeX expressions to KaTeX HTML.
- `scripts/package.json` — `katex` npm dependency

### Frontend

- New `<RichContent html={body_html} />` component replaces raw
  `dangerouslySetInnerHTML` across post detail, answer cards, and comment
  nodes. Renders the HTML and mounts Mermaid when needed.
- `<MermaidBlock>` component with dynamic import
- `public/fonts/katex/` — font files + CSS
- `pygments-theme.css` — global token colors for highlighted code

### No database migration

`body_html` is still `Text`. The HTML just gets richer content.

### Existing posts

**Lazy re-render:** existing posts keep their current `body_html` until
next edit, at which point the new `renderer.py` produces highlighted/math
output. A backfill script can be run manually later if needed.

## Out of scope

- Live math/diagram preview in the editor
- Light/dark theme toggle for code blocks
- Mermaid toolbar button
- Backfill migration script (can be added later as a standalone task)
