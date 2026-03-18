"""Tests for contradiction detector."""

from __future__ import annotations

from fougasse.graph.contradiction_detector import (
    apply_contradiction,
    check_negation,
    detect_contradiction,
)
from fougasse.graph.knowledge_graph import KnowledgeGraph


def test_check_negation_english() -> None:
    assert check_negation("The meeting is on Monday", "The meeting is not on Monday")
    assert check_negation("Use Python", "Actually, use Rust instead")
    assert check_negation("Deploy to prod", "Cancel the deployment")


def test_check_negation_french() -> None:
    assert check_negation("La reunion est lundi", "La reunion n'est pas lundi")
    assert check_negation("Utiliser Python", "En fait, utiliser Rust")


def test_check_negation_no_negation() -> None:
    assert not check_negation("Python is great", "Python is powerful")
    assert not check_negation("Meeting at 3pm", "Meeting at 3pm sharp")


def test_detect_contradiction_supersedes() -> None:
    result = detect_contradiction(
        "The API endpoint is /v2/users",
        [("mem-old", 0.90, "The API endpoint is not /v1/users")],
        similarity_threshold=0.85,
    )
    assert result.has_contradiction
    assert result.relation_type == "supersedes"
    assert result.conflicting_memory_id == "mem-old"


def test_detect_contradiction_very_high_similarity() -> None:
    result = detect_contradiction(
        "Deploy to production on Friday",
        [("mem-dup", 0.97, "Deploy to production on Friday afternoon")],
    )
    assert result.has_contradiction
    assert result.relation_type == "conflicts_with"


def test_detect_no_contradiction() -> None:
    result = detect_contradiction(
        "Python is great for ML",
        [("mem-1", 0.5, "Rust is fast")],
    )
    assert not result.has_contradiction


def test_detect_below_threshold() -> None:
    result = detect_contradiction(
        "Something new",
        [("mem-1", 0.80, "Something old and not related")],
        similarity_threshold=0.85,
    )
    assert not result.has_contradiction


def test_apply_contradiction() -> None:
    from fougasse.graph.contradiction_detector import ContradictionResult

    kg = KnowledgeGraph()
    kg.add_memory_node("new", "New content")
    kg.add_memory_node("old", "Old content")

    result = ContradictionResult(
        has_contradiction=True,
        conflicting_memory_id="old",
        similarity=0.92,
        relation_type="supersedes",
    )
    apply_contradiction(kg, "new", result)
    assert kg.has_edge("new", "old")
