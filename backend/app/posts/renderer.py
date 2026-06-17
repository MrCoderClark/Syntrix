from __future__ import annotations

from html import escape


def render_tiptap_json(doc: dict) -> str:
    if doc.get("type") != "doc":
        return ""
    return _render_nodes(doc.get("content", []))


def _render_nodes(nodes: list[dict]) -> str:
    return "".join(_render_node(n) for n in nodes)


def _render_node(node: dict) -> str:
    t = node.get("type", "")
    attrs = node.get("attrs", {})
    content = node.get("content", [])

    if t == "text":
        text = escape(node.get("text", ""))
        for mark in node.get("marks", []):
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
        lang = escape(attrs.get("language", "")) if attrs.get("language") else ""
        code = _render_nodes(content)
        cls = f' class="language-{lang}"' if lang else ""
        return f"<pre><code{cls}>{code}</code></pre>"

    if t == "bulletList":
        return f"<ul>{_render_nodes(content)}</ul>"

    if t == "orderedList":
        start = attrs.get("start", 1)
        start_attr = f' start="{start}"' if start != 1 else ""
        return f"<ol{start_attr}>{_render_nodes(content)}</ol>"

    if t == "listItem":
        return f"<li>{_render_nodes(content)}</li>"

    if t == "image":
        src = escape(attrs.get("src", ""))
        alt = escape(attrs.get("alt", ""))
        return f'<img src="{src}" alt="{alt}" />'

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
