import pytest

from app.comments.tree import MAX_DEPTH, build_comment_tree, compute_path, depth_from_path


def test_root_comment_path():
    assert compute_path(parent_path=None, comment_id_hex="a1b2c3d4") == "a1b2c3d4"


def test_reply_path():
    assert compute_path(parent_path="a1b2c3d4", comment_id_hex="e5f6a7b8") == "a1b2c3d4.e5f6a7b8"


def test_nested_reply_path():
    path = compute_path(parent_path="a1b2c3d4.e5f6a7b8", comment_id_hex="c9d0e1f2")
    assert path == "a1b2c3d4.e5f6a7b8.c9d0e1f2"


def test_depth_from_path():
    assert depth_from_path("a1b2c3d4") == 1
    assert depth_from_path("a1b2c3d4.e5f6a7b8") == 2
    assert depth_from_path("a.b.c.d.e") == 5


def test_max_depth_exceeded():
    deep_path = ".".join([f"n{i}" for i in range(MAX_DEPTH)])
    with pytest.raises(ValueError, match="depth"):
        compute_path(parent_path=deep_path, comment_id_hex="tooDeep")


def test_build_tree_flat():
    rows = [
        {"id": "a", "path": "a", "depth": 1, "body_html": "root 1"},
        {"id": "b", "path": "b", "depth": 1, "body_html": "root 2"},
    ]
    tree = build_comment_tree(rows)
    assert len(tree) == 2
    assert tree[0]["children"] == []
    assert tree[1]["children"] == []


def test_build_tree_nested():
    rows = [
        {"id": "a", "path": "a", "depth": 1, "body_html": "root"},
        {"id": "b", "path": "a.b", "depth": 2, "body_html": "reply"},
        {"id": "c", "path": "a.b.c", "depth": 3, "body_html": "reply reply"},
    ]
    tree = build_comment_tree(rows)
    assert len(tree) == 1
    assert len(tree[0]["children"]) == 1
    assert len(tree[0]["children"][0]["children"]) == 1
