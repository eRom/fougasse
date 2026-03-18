"""Tests for FTS5 full-text search operations."""

from __future__ import annotations

import pytest

from fougasse.storage.database import init_database
from fougasse.storage.fts_store import index_memory, remove_from_index, search_bm25


@pytest.fixture
def db():
    conn = init_database()
    yield conn
    conn.close()


def _populate(db) -> None:
    """Insert sample data for testing."""
    index_memory(db, "mem-1", "Python is a great programming language", ["python", "coding"])
    index_memory(db, "mem-2", "Rust is fast and memory safe", ["rust", "coding"])
    index_memory(db, "mem-3", "Docker containers for deployment", ["docker", "devops"])
    index_memory(db, "mem-4", "Python web framework Flask", ["python", "flask", "web"])
    index_memory(db, "mem-5", "Machine learning with PyTorch", ["python", "ml", "pytorch"])


def test_search_basic(db) -> None:
    _populate(db)
    results = search_bm25(db, "Python", limit=10)
    assert len(results) >= 2
    # All results should contain "Python" related content
    memory_ids = [r[0] for r in results]
    assert "mem-1" in memory_ids
    assert "mem-4" in memory_ids


def test_search_multi_term(db) -> None:
    _populate(db)
    results = search_bm25(db, "Python web", limit=5)
    assert len(results) >= 1
    # mem-4 should be most relevant (both terms)
    assert results[0][0] == "mem-4"


def test_search_tags(db) -> None:
    _populate(db)
    results = search_bm25(db, "devops", limit=5)
    assert len(results) >= 1
    assert results[0][0] == "mem-3"


def test_search_no_results(db) -> None:
    _populate(db)
    results = search_bm25(db, "nonexistentterm12345", limit=5)
    assert len(results) == 0


def test_search_empty_db(db) -> None:
    results = search_bm25(db, "anything", limit=5)
    assert len(results) == 0


def test_remove_from_index(db) -> None:
    _populate(db)
    remove_from_index(db, "mem-1")
    results = search_bm25(db, "Python programming language", limit=10)
    memory_ids = [r[0] for r in results]
    assert "mem-1" not in memory_ids


def test_reindex(db) -> None:
    index_memory(db, "mem-1", "Original content", ["old-tag"])
    index_memory(db, "mem-1", "Updated content about Rust", ["rust"])
    results = search_bm25(db, "Rust", limit=5)
    assert any(r[0] == "mem-1" for r in results)
    results_old = search_bm25(db, "Original", limit=5)
    assert not any(r[0] == "mem-1" for r in results_old)
