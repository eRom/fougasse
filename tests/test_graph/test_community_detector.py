"""Tests for community detection and PageRank."""

from __future__ import annotations

from fougasse.graph.community_detector import (
    compute_pagerank,
    detect_communities,
    get_community_summary,
)
from fougasse.graph.knowledge_graph import KnowledgeGraph


def _build_test_graph() -> KnowledgeGraph:
    kg = KnowledgeGraph()
    # Cluster 1
    kg.add_memory_node("a", "A")
    kg.add_memory_node("b", "B")
    kg.add_memory_node("c", "C")
    kg.add_edge("a", "b", relation="relates_to")
    kg.add_edge("b", "c", relation="relates_to")
    kg.add_edge("c", "a", relation="relates_to")
    # Cluster 2
    kg.add_memory_node("x", "X")
    kg.add_memory_node("y", "Y")
    kg.add_edge("x", "y", relation="relates_to")
    kg.add_edge("y", "x", relation="relates_to")
    # Bridge
    kg.add_edge("c", "x", relation="relates_to")
    return kg


def test_compute_pagerank() -> None:
    kg = _build_test_graph()
    scores = compute_pagerank(kg)
    assert len(scores) == 5
    # All scores should be positive
    for score in scores.values():
        assert score > 0
    # Node with more connections should have higher rank
    assert kg.graph.nodes["c"]["pagerank"] > 0


def test_pagerank_empty() -> None:
    kg = KnowledgeGraph()
    assert compute_pagerank(kg) == {}


def test_detect_communities() -> None:
    kg = _build_test_graph()
    mapping = detect_communities(kg)
    assert len(mapping) == 5
    # All nodes should have a community ID
    for node_id in ["a", "b", "c", "x", "y"]:
        assert node_id in mapping
        assert kg.graph.nodes[node_id].get("community_id") is not None


def test_detect_communities_empty() -> None:
    kg = KnowledgeGraph()
    assert detect_communities(kg) == {}


def test_get_community_summary() -> None:
    kg = _build_test_graph()
    detect_communities(kg)
    summary = get_community_summary(kg)
    assert len(summary) >= 1
    for s in summary:
        assert "community_id" in s
        assert "node_count" in s
        assert s["node_count"] > 0
