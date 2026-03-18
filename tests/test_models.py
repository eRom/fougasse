"""Tests for Pydantic models."""

from __future__ import annotations

import pytest

from fougasse.models import (
    FougasseStatus,
    MemoryCreate,
    MemoryType,
    SearchQuery,
    VaultCreate,
    utcnow,
)


def test_memory_create_valid() -> None:
    m = MemoryCreate(content="Test memory", type=MemoryType.TEXT, tags=["python", "test"])
    assert m.content == "Test memory"
    assert m.type == MemoryType.TEXT
    assert m.tags == ["python", "test"]
    assert m.vault_id == "default"


def test_memory_create_tags_lowercase() -> None:
    m = MemoryCreate(content="Test", tags=["Python", "RUST"])
    assert m.tags == ["python", "rust"]


def test_memory_create_empty_content_fails() -> None:
    with pytest.raises(Exception):
        MemoryCreate(content="")


def test_memory_create_invalid_tag_fails() -> None:
    with pytest.raises(Exception):
        MemoryCreate(content="Test", tags=["invalid tag with spaces!"])


def test_memory_create_tag_too_long_fails() -> None:
    with pytest.raises(Exception):
        MemoryCreate(content="Test", tags=["a" * 65])


def test_memory_create_invalid_vault_fails() -> None:
    with pytest.raises(Exception):
        MemoryCreate(content="Test", vault_id="has spaces!")


def test_memory_types() -> None:
    for t in MemoryType:
        m = MemoryCreate(content="Test", type=t)
        assert m.type == t


def test_search_query_defaults() -> None:
    q = SearchQuery(query="find something")
    assert q.limit == 10
    assert q.vault_id is None
    assert q.include_archived is False


def test_search_query_limits() -> None:
    with pytest.raises(Exception):
        SearchQuery(query="test", limit=0)
    with pytest.raises(Exception):
        SearchQuery(query="test", limit=101)


def test_vault_create() -> None:
    v = VaultCreate(name="my-project", description="A project vault")
    assert v.name == "my-project"


def test_vault_create_invalid_name() -> None:
    with pytest.raises(Exception):
        VaultCreate(name="has spaces")


def test_fougasse_status() -> None:
    s = FougasseStatus(version="0.1.0", memory_count=42, vault_count=2)
    assert s.version == "0.1.0"
    assert s.memory_count == 42


def test_utcnow() -> None:
    now = utcnow()
    assert now.tzinfo is not None
