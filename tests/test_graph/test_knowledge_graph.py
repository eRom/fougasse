"""Tests for knowledge graph core."""

from __future__ import annotations

import pytest

from fougasse.graph.knowledge_graph import KnowledgeGraph


def test_add_memory_node() -> None:
    kg = KnowledgeGraph()
    kg.add_memory_node("mem-1", "Test memory")
    assert kg.has_node("mem-1")
    attrs = kg.get_node_attrs("mem-1")
    assert attrs["node_type"] == "memory"
    assert attrs["label"] == "Test memory"


def test_add_entity_node() -> None:
    kg = KnowledgeGraph()
    kg.add_entity_node("tag:python", "python")
    assert kg.has_node("tag:python")
    assert kg.get_node_attrs("tag:python")["node_type"] == "entity"


def test_add_edge() -> None:
    kg = KnowledgeGraph()
    kg.add_memory_node("mem-1", "Memory 1")
    kg.add_entity_node("tag:python", "python")
    kg.add_edge("mem-1", "tag:python", relation="tagged_with")
    assert kg.has_edge("mem-1", "tag:python")
    assert kg.edge_count == 1


def test_add_edge_invalid_relation() -> None:
    kg = KnowledgeGraph()
    kg.add_memory_node("a", "A")
    kg.add_memory_node("b", "B")
    with pytest.raises(ValueError, match="Invalid relation"):
        kg.add_edge("a", "b", relation="invalid_relation")


def test_remove_node() -> None:
    kg = KnowledgeGraph()
    kg.add_memory_node("mem-1", "Test")
    assert kg.remove_node("mem-1") is True
    assert not kg.has_node("mem-1")
    assert kg.remove_node("nonexistent") is False


def test_remove_edge() -> None:
    kg = KnowledgeGraph()
    kg.add_memory_node("a", "A")
    kg.add_memory_node("b", "B")
    kg.add_edge("a", "b", relation="relates_to")
    assert kg.remove_edge("a", "b") is True
    assert not kg.has_edge("a", "b")


def test_get_neighbors() -> None:
    kg = KnowledgeGraph()
    kg.add_memory_node("center", "Center")
    kg.add_memory_node("n1", "Neighbor 1")
    kg.add_memory_node("n2", "Neighbor 2")
    kg.add_memory_node("n3", "Depth 2")
    kg.add_edge("center", "n1", relation="relates_to")
    kg.add_edge("center", "n2", relation="relates_to")
    kg.add_edge("n1", "n3", relation="relates_to")

    neighbors_d1 = kg.get_neighbors("center", depth=1)
    assert len(neighbors_d1) == 2

    neighbors_d2 = kg.get_neighbors("center", depth=2)
    assert len(neighbors_d2) == 3


def test_get_subgraph() -> None:
    kg = KnowledgeGraph()
    kg.add_memory_node("a", "A")
    kg.add_memory_node("b", "B")
    kg.add_memory_node("c", "C")
    kg.add_edge("a", "b", relation="relates_to")
    kg.add_edge("b", "c", relation="relates_to")

    sub = kg.get_subgraph("a", depth=2)
    assert len(sub["nodes"]) == 3
    assert len(sub["edges"]) == 2


def test_counts() -> None:
    kg = KnowledgeGraph()
    assert kg.node_count == 0
    assert kg.edge_count == 0
    kg.add_memory_node("a", "A")
    kg.add_memory_node("b", "B")
    kg.add_edge("a", "b", relation="relates_to")
    assert kg.node_count == 2
    assert kg.edge_count == 1
