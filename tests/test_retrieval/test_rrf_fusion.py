"""Tests for RRF fusion."""

from __future__ import annotations

from fougasse.retrieval.rrf_fusion import rrf_fuse


def test_single_list() -> None:
    results = rrf_fuse([[("a", 1.0), ("b", 0.5), ("c", 0.1)]])
    assert results[0][0] == "a"
    assert results[1][0] == "b"
    assert results[2][0] == "c"


def test_two_lists_agreement() -> None:
    list1 = [("a", 1.0), ("b", 0.5)]
    list2 = [("a", 0.9), ("b", 0.4)]
    results = rrf_fuse([list1, list2])
    # Both lists agree: a > b
    assert results[0][0] == "a"
    assert results[1][0] == "b"


def test_two_lists_disagreement() -> None:
    list1 = [("a", 1.0), ("b", 0.5)]
    list2 = [("b", 0.9), ("c", 0.4)]
    results = rrf_fuse([list1, list2])
    ids = [r[0] for r in results]
    # b appears in both lists, should rank high
    assert "b" in ids[:2]


def test_weighted_fusion() -> None:
    list1 = [("a", 1.0)]
    list2 = [("b", 1.0)]
    # Heavy weight on list2
    results = rrf_fuse([list1, list2], weights=[1.0, 10.0])
    assert results[0][0] == "b"  # list2 wins


def test_empty_lists() -> None:
    assert rrf_fuse([]) == []
    assert rrf_fuse([[]]) == []


def test_custom_k() -> None:
    list1 = [("a", 1.0)]
    results_low_k = rrf_fuse([list1], k=1)
    results_high_k = rrf_fuse([list1], k=100)
    # Lower k gives higher scores
    assert results_low_k[0][1] > results_high_k[0][1]
