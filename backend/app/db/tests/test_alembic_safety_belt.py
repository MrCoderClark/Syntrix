import pathlib
import re

import pytest
from sqlalchemy import Column, Integer, MetaData, Table

_env_path = pathlib.Path(__file__).resolve().parents[3] / "alembic" / "env.py"
_source = _env_path.read_text()


def _load_filters():
    # Extract only the SAFE_SCHEMA constant and the two filter functions
    ns: dict = {}
    # Get SAFE_SCHEMA
    match = re.search(r'^SAFE_SCHEMA\s*=\s*"(\w+)"', _source, re.MULTILINE)
    ns["SAFE_SCHEMA"] = match.group(1)

    # Extract include_name function
    include_name_match = re.search(r"(def include_name\(.*?\n(?:    .*\n)*)", _source, re.MULTILINE)
    exec(include_name_match.group(1), ns)  # noqa: S102

    # Extract include_object function
    include_object_match = re.search(
        r"(def include_object\(.*?\n(?:    .*\n)*)", _source, re.MULTILINE
    )
    exec(include_object_match.group(1), ns)  # noqa: S102

    return ns["include_object"], ns["include_name"]


include_object, include_name = _load_filters()


def _table_in_schema(schema: str, name: str = "users") -> Table:
    md = MetaData(schema=schema)
    return Table(name, md, Column("id", Integer, primary_key=True))


def test_include_object_allows_syntrix():
    tbl = _table_in_schema("syntrix")
    assert include_object(tbl, "users", "table", False, None) is True


def test_include_object_raises_on_auth_schema():
    tbl = _table_in_schema("auth")
    with pytest.raises(RuntimeError, match="auth"):
        include_object(tbl, "users", "table", False, None)


def test_include_object_raises_on_public_schema():
    tbl = _table_in_schema("public")
    with pytest.raises(RuntimeError, match="public"):
        include_object(tbl, "anything", "table", False, None)


def test_include_object_allows_unschemed():
    class Bare:
        pass

    obj = Bare()
    assert include_object(obj, "ix_anything", "index", False, None) is True


def test_include_name_filters_schemas_to_syntrix_only():
    assert include_name("syntrix", "schema", {}) is True
    assert include_name("auth", "schema", {}) is False
    assert include_name("public", "schema", {}) is False
    assert include_name("users", "table", {"schema_name": "syntrix"}) is True
