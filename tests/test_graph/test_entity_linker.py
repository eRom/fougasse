"""Tests for entity linker."""

from __future__ import annotations

from fougasse.graph.entity_linker import link_by_similarity, link_memory
from fougasse.graph.knowledge_graph import KnowledgeGraph
from fougasse.models import Memory, MemoryType, utcnow


def _make_memory(id: str, content: str, tags: list[str]) -> Memory:
    now = utcnow()
    return Memory(
        id=id, content=content, type=MemoryType.TEXT, tags=tags,
        vault_id="default", created_at=now, updated_at=now,
    )


def test_link_memory_tags() -> None:
    kg = KnowledgeGraph()
    mem = _make_memory("mem-1", "Python tutorial", ["python", "tutorial"])
    edges = link_memory(kg, mem)
    assert edges == 2  # 2 tagged_with edges
    assert kg.has_node("tag:python")
    assert kg.has_node("tag:tutorial")
    assert kg.has_edge("mem-1", "tag:python")


def test_link_shared_tags() -> None:
    kg = KnowledgeGraph()
    mem1 = _make_memory("mem-1", "Python ML", ["python", "ml", "data"])
    mem2 = _make_memory("mem-2", "Python Data Science", ["python", "data", "science"])

    link_memory(kg, mem1)
    link_memory(kg, mem2)

    # Should have relates_to between mem-1 and mem-2 (share python + data)
    assert kg.has_edge("mem-1", "mem-2") or kg.has_edge("mem-2", "mem-1")


def test_link_by_similarity() -> None:
    kg = KnowledgeGraph()
    kg.add_memory_node("mem-1", "A")
    kg.add_memory_node("mem-2", "B")
    kg.add_memory_node("mem-3", "C")

    # distance 0.1 → similarity ~0.95
    similar = [("mem-2", 0.1), ("mem-3", 1.5)]
    created = link_by_similarity(kg, "mem-1", similar, threshold=0.8)
    assert created == 1  # Only mem-2 is similar enough
    assert kg.has_edge("mem-1", "mem-2")
    assert not kg.has_edge("mem-1", "mem-3")
