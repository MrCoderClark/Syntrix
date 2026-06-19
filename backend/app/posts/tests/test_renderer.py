from app.posts.renderer import render_tiptap_json


def test_paragraph():
    doc = {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Hello world"}]}],
    }
    assert "<p>Hello world</p>" in render_tiptap_json(doc)


def test_heading():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Title"}],
            }
        ],
    }
    assert "<h2>Title</h2>" in render_tiptap_json(doc)


def test_bold_italic():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "marks": [{"type": "bold"}], "text": "strong"},
                    {"type": "text", "marks": [{"type": "italic"}], "text": "emphasis"},
                ],
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert "<strong>strong</strong>" in html
    assert "<em>emphasis</em>" in html


def test_code_block():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "codeBlock",
                "attrs": {"language": "python"},
                "content": [{"type": "text", "text": "print('hi')"}],
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert '<pre class="highlight">' in html
    assert "print" in html


def test_code_block_highlighted():
    """Pygments should produce span tokens for known languages."""
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "codeBlock",
                "attrs": {"language": "python"},
                "content": [{"type": "text", "text": "def hello():\n    pass"}],
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert '<pre class="highlight">' in html
    assert "<span" in html
    assert "def" in html
    assert "hello" in html


def test_code_block_unknown_language():
    """Unknown languages fall back to plain text, no crash."""
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "codeBlock",
                "attrs": {"language": "notareallang"},
                "content": [{"type": "text", "text": "some code"}],
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert '<pre class="highlight">' in html
    assert "some code" in html


def test_code_block_no_language():
    """Code blocks with no language get plain rendering."""
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "codeBlock",
                "attrs": {},
                "content": [{"type": "text", "text": "plain text"}],
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert '<pre class="highlight">' in html
    assert "plain text" in html


def test_code_block_xss_in_language():
    """Language attr with XSS payload must not inject HTML."""
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "codeBlock",
                "attrs": {"language": '"><script>alert(1)</script>'},
                "content": [{"type": "text", "text": "x"}],
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert "<script>" not in html


def test_image():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "image",
                "attrs": {"src": "https://example.com/img.jpg", "alt": "photo"},
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert "<img " in html
    assert 'src="https://example.com/img.jpg"' in html


def test_xss_escape():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "<script>alert(1)</script>"}],
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_empty_doc():
    doc = {"type": "doc", "content": []}
    assert render_tiptap_json(doc) == ""


def test_link_mark():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "marks": [{"type": "link", "attrs": {"href": "https://example.com"}}],
                        "text": "click",
                    }
                ],
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert 'href="https://example.com"' in html
    assert 'rel="noopener"' in html


def test_list():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "item"}],
                            }
                        ],
                    }
                ],
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert "<ul>" in html
    assert "<li>" in html


def test_iframe_allowed_host():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "iframe",
                "attrs": {"src": "http://localhost:3007/embed/abc123"},
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert '<div class="iframe-wrap">' in html
    assert "<iframe " in html
    assert "localhost:3007/embed/abc123" in html


def test_iframe_blocked_host():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "iframe",
                "attrs": {"src": "https://evil.com/exploit"},
            }
        ],
    }
    html = render_tiptap_json(doc)
    assert "<iframe" not in html
    assert "<a " in html
    assert "evil.com/exploit" in html
