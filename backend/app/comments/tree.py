from __future__ import annotations

MAX_DEPTH = 10


def compute_path(parent_path: str | None, comment_id_hex: str) -> str:
    if parent_path is None:
        return comment_id_hex
    depth = parent_path.count(".") + 2
    if depth > MAX_DEPTH:
        raise ValueError(f"Comment depth {depth} exceeds max {MAX_DEPTH}")
    return f"{parent_path}.{comment_id_hex}"


def depth_from_path(path: str) -> int:
    return path.count(".") + 1


def build_comment_tree(rows: list[dict]) -> list[dict]:
    nodes: dict[str, dict] = {}
    roots: list[dict] = []

    for row in rows:
        node = {**row, "children": []}
        nodes[row["path"]] = node

        if row["depth"] == 1:
            roots.append(node)
        else:
            parent_path = row["path"].rsplit(".", 1)[0]
            parent = nodes.get(parent_path)
            if parent:
                parent["children"].append(node)
            else:
                roots.append(node)

    return roots
