"""Tests for hybrid search (P0: 2 channels)."""

from __future__ import annotations

import pytest

from fougasse.models import MemoryCreate, MemoryType, SearchQuery
from fougasse.retrieval.hybrid_search import hybrid_search
from fougasse.storage.database import init_database
from fougasse.storage.fts_store import index_memory
from fougasse.storage.memory_store import insert_memory
from fougasse.storage.vector_store import ensure_vec_table, insert_vector


# Mock embedding: returns a simple vector based on content hash
def _mock_embed(text: str) -> list[float]:
    """Deterministic mock embedding for testing."""
    vec = [0.0] * 4
    words = text.lower().split()
    for i, w in enumerate(words[:4]):
        vec[i % 4] += hash(w) % 100 / 100.0
    # Normalize
    mag = sum(v * v for v in vec) ** 0.5
    if mag > 0:
        vec = [v / mag for v in vec]
    return vec


@pytest.fixture
def db():
    conn = init_database()
    ensure_vec_table(conn, dim=4)
    yield conn
    conn.close()


def _populate(db):
    """Insert test memories with embeddings and FTS index."""
    memories = [
        ("Python is great for machine learning", MemoryType.CODE, ["python", "ml"]),
        ("Rust is fast and memory safe", MemoryType.CODE, ["rust", "systems"]),
        ("Meeting tomorrow at 3pm to discuss architecture", MemoryType.APPOINTMENT, ["meeting"]),
        ("Idea: build a knowledge graph for memory", MemoryType.IDEA, ["graph", "memory"]),
        ("Docker deployment pipeline for production", MemoryType.TEXT, ["docker", "devops"]),
    ]
    for content, mtype, tags in memories:
        mem = insert_memory(db, MemoryCreate(content=content, type=mtype, tags=tags))
        embedding = _mock_embed(content)
        insert_vector(db, mem.id, mem.vault_id, embedding)
        index_memory(db, mem.id, content, tags)


def test_hybrid_search_basic(db) -> None:
    _populate(db)
    result = hybrid_search(
        db,
        SearchQuery(query="Python machine learning"),
        embed_fn=_mock_embed,
    )
    assert result.total_count > 0
    assert result.search_time_ms > 0
    # Python ML memory should be in results
    contents = [r.memory.content for r in result.results]
    assert any("Python" in c for c in contents)


def test_hybrid_search_type_filter(db) -> None:
    _populate(db)
    result = hybrid_search(
        db,
        SearchQuery(query="Python", type_filter=MemoryType.CODE),
        embed_fn=_mock_embed,
    )
    for r in result.results:
        assert r.memory.type == MemoryType.CODE


def test_hybrid_search_empty_db(db) -> None:
    result = hybrid_search(
        db,
        SearchQuery(query="anything"),
        embed_fn=_mock_embed,
    )
    assert result.total_count == 0


def test_hybrid_search_match_sources(db) -> None:
    _populate(db)
    result = hybrid_search(
        db,
        SearchQuery(query="Docker deployment"),
        embed_fn=_mock_embed,
    )
    if result.results:
        # At least one source should be identified
        for r in result.results:
            assert len(r.match_sources) > 0


def test_hybrid_search_limit(db) -> None:
    _populate(db)
    result = hybrid_search(
        db,
        SearchQuery(query="is", limit=2),
        embed_fn=_mock_embed,
    )
    assert len(result.results) <= 2
