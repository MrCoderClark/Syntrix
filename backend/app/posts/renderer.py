from __future__ import annotations

import json
import re
import subprocess
from html import escape
from pathlib import Path
from urllib.parse import urlparse

from pygments import highlight as pygments_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

_KATEX_SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "render-katex.mjs"

ALLOWED_IFRAME_HOSTS = {
    "www.youtube.com",
    "youtube.com",
    "www.youtube-nocookie.com",
    "player.vimeo.com",
    "www.twitch.tv",
    "clips.twitch.tv",
    "player.twitch.tv",
    "www.dailymotion.com",
    "streamable.com",
    "codepen.io",
    "codesandbox.io",
    "localhost",
    "127.0.0.1",
}


def render_tiptap_json(doc: dict) -> str:
    if doc.get("type") != "doc":
        return ""
    return _render_nodes(doc.get("content", []))


def _render_nodes(nodes: list[dict]) -> str:
    return "".join(_render_node(n) for n in nodes)


def _extract_text(nodes: list[dict]) -> str:
    """Extract raw text from TipTap content nodes (used for code blocks)."""
    parts: list[str] = []
    for node in nodes:
        if node.get("type") == "text":
            parts.append(node.get("text", ""))
        elif "content" in node:
            parts.append(_extract_text(node["content"]))
    return "".join(parts)


_MATH_BLOCK = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
_MATH_INLINE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)")
_ESCAPED_DOLLAR = re.compile(r"\\\$")


def _parse_math(text: str) -> list[dict]:
    """Find all math expressions in text, return list of {latex, displayMode, start, end}."""
    placeholder = "\x00ESCAPED_DOLLAR\x00"
    working = _ESCAPED_DOLLAR.sub(placeholder, text)

    spans: list[dict] = []
    for m in _MATH_BLOCK.finditer(working):
        spans.append(
            {
                "latex": m.group(1).strip(),
                "displayMode": True,
                "start": m.start(),
                "end": m.end(),
            }
        )
    for m in _MATH_INLINE.finditer(working):
        if any(s["start"] <= m.start() < s["end"] for s in spans):
            continue
        spans.append(
            {
                "latex": m.group(1).strip(),
                "displayMode": False,
                "start": m.start(),
                "end": m.end(),
            }
        )
    spans.sort(key=lambda s: s["start"])
    return spans


def _render_math_batch(expressions: list[dict]) -> list[str]:
    """Call the Node KaTeX helper to batch-render math expressions."""
    if not expressions:
        return []
    payload = json.dumps(
        [{"latex": e["latex"], "displayMode": e["displayMode"]} for e in expressions]
    )
    try:
        result = subprocess.run(  # noqa: S603
            ["node", str(_KATEX_SCRIPT)],  # noqa: S607
            input=payload,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return [f'<code class="math-error">{escape(e["latex"])}</code>' for e in expressions]
        items = json.loads(result.stdout)
        rendered: list[str] = []
        for item, expr in zip(items, expressions, strict=False):
            if item.get("error") or not item.get("html"):
                rendered.append(f'<code class="math-error">{escape(expr["latex"])}</code>')
            elif expr["displayMode"]:
                rendered.append(f'<div class="math-block">{item["html"]}</div>')
            else:
                rendered.append(item["html"])
        return rendered
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return [f'<code class="math-error">{escape(e["latex"])}</code>' for e in expressions]


def _apply_math_to_text(text: str) -> str:
    """Replace $...$ and $$...$$ in a plain text string with rendered KaTeX HTML."""
    placeholder = "\x00ESCAPED_DOLLAR\x00"
    working = _ESCAPED_DOLLAR.sub(placeholder, text)

    spans = _parse_math(text)
    if not spans:
        return escape(working).replace(placeholder, "$")

    rendered = _render_math_batch(spans)

    parts: list[str] = []
    prev_end = 0
    for span, html in zip(spans, rendered, strict=False):
        parts.append(escape(working[prev_end : span["start"]]))
        parts.append(html)
        prev_end = span["end"]
    parts.append(escape(working[prev_end:]))

    result = "".join(parts)
    return result.replace(placeholder, "$")


def _render_node(node: dict) -> str:
    t = node.get("type", "")
    attrs = node.get("attrs", {})
    content = node.get("content", [])

    if t == "text":
        raw = node.get("text", "")
        marks = node.get("marks", [])
        if not marks:
            return _apply_math_to_text(raw)
        text = escape(raw)
        for mark in marks:
            text = _apply_mark(text, mark)
        return text

    if t == "paragraph":
        return f"<p>{_render_nodes(content)}</p>"

    if t == "heading":
        level = min(max(attrs.get("level", 1), 1), 6)
        return f"<h{level}>{_render_nodes(content)}</h{level}>"

    if t == "blockquote":
        return f"<blockquote>{_render_nodes(content)}</blockquote>"

    if t == "codeBlock":
        lang = attrs.get("language", "") or ""
        code_text = _extract_text(content)
        try:
            lexer = get_lexer_by_name(lang) if lang else TextLexer()
        except ClassNotFound:
            lexer = TextLexer()
        formatter = HtmlFormatter(nowrap=True)
        highlighted = pygments_highlight(code_text, lexer, formatter)
        return f'<pre class="highlight"><code>{highlighted}</code></pre>'

    if t == "bulletList":
        return f"<ul>{_render_nodes(content)}</ul>"

    if t == "orderedList":
        start = attrs.get("start", 1)
        start_attr = f' start="{start}"' if start != 1 else ""
        return f"<ol{start_attr}>{_render_nodes(content)}</ol>"

    if t == "listItem":
        return f"<li>{_render_nodes(content)}</li>"

    if t == "image":
        src = escape(attrs.get("src") or "")
        alt = escape(attrs.get("alt") or "")
        return f'<img src="{src}" alt="{alt}" />'

    if t == "iframe":
        src = attrs.get("src") or ""
        parsed = urlparse(src)
        if parsed.hostname not in ALLOWED_IFRAME_HOSTS:
            return (
                f'<p><a href="{escape(src)}" target="_blank" rel="noopener">{escape(src)}</a></p>'
            )
        safe_src = escape(src)
        return (
            f'<div class="iframe-wrap">'
            f'<iframe src="{safe_src}" frameborder="0" allowfullscreen></iframe>'
            f"</div>"
        )

    if t == "hardBreak":
        return "<br />"

    if t == "horizontalRule":
        return "<hr />"

    if t == "table":
        return f"<table>{_render_nodes(content)}</table>"

    if t == "tableRow":
        return f"<tr>{_render_nodes(content)}</tr>"

    if t == "tableCell":
        return f"<td>{_render_nodes(content)}</td>"

    if t == "tableHeader":
        return f"<th>{_render_nodes(content)}</th>"

    return _render_nodes(content)


def _apply_mark(text: str, mark: dict) -> str:
    t = mark.get("type", "")
    attrs = mark.get("attrs", {})

    if t == "bold":
        return f"<strong>{text}</strong>"
    if t == "italic":
        return f"<em>{text}</em>"
    if t == "strike":
        return f"<s>{text}</s>"
    if t == "code":
        return f"<code>{text}</code>"
    if t == "link":
        href = escape(attrs.get("href", ""))
        return f'<a href="{href}" target="_blank" rel="noopener">{text}</a>'

    return text
