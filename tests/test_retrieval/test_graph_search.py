"""Tests for graph-based retrieval."""

from __future__ import annotations

from fougasse.graph.knowledge_graph import KnowledgeGraph
from fougasse.retrieval.graph_search import spreading_activation


def _build_graph() -> KnowledgeGraph:
    kg = KnowledgeGraph()
    kg.add_memory_node("seed", "Seed memory")
    kg.add_memory_node("hop1a", "Hop 1 A")
    kg.add_memory_node("hop1b", "Hop 1 B")
    kg.add_memory_node("hop2", "Hop 2")
    kg.add_entity_node("tag:python", "python")

    kg.add_edge("seed", "hop1a", relation="relates_to", weight=1.0)
    kg.add_edge("seed", "hop1b", relation="relates_to", weight=0.5)
    kg.add_edge("hop1a", "hop2", relation="relates_to", weight=1.0)
    kg.add_edge("seed", "tag:python", relation="tagged_with")
    return kg


def test_spreading_activation_basic() -> None:
    kg = _build_graph()
    results = spreading_activation(kg, ["seed"], max_hops=2)
    ids = [r[0] for r in results]
    # hop1a and hop1b should be found (memory type)
    assert "hop1a" in ids
    assert "hop1b" in ids
    # tag:python should NOT be in results (entity type)
    assert "tag:python" not in ids


def test_spreading_activation_scores() -> None:
    kg = _build_graph()
    results = spreading_activation(kg, ["seed"], max_hops=2, decay=0.5)
    scores = {r[0]: r[1] for r in results}
    # hop1a (weight=1.0) should score higher than hop1b (weight=0.5)
    assert scores.get("hop1a", 0) >= scores.get("hop1b", 0)


def test_spreading_activation_depth() -> None:
    kg = _build_graph()
    results_1 = spreading_activation(kg, ["seed"], max_hops=1)
    results_2 = spreading_activation(kg, ["seed"], max_hops=2)
    # Deeper hops should find more nodes
    assert len(results_2) >= len(results_1)


def test_spreading_activation_empty() -> None:
    kg = KnowledgeGraph()
    results = spreading_activation(kg, ["nonexistent"])
    assert results == []


def test_spreading_activation_excludes_seeds() -> None:
    kg = _build_graph()
    results = spreading_activation(kg, ["seed"])
    ids = [r[0] for r in results]
    assert "seed" not in ids
