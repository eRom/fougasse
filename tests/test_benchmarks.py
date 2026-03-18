"""Tests for built-in benchmarks."""

from __future__ import annotations

from fougasse.benchmarks.retrieval_bench import run_benchmark


def test_benchmark_small() -> None:
    result = run_benchmark(count=50, queries=10, dim=4)
    assert result["memories"] == 50
    assert result["queries"] == 10
    assert result["retrieval_p50_ms"] > 0
    assert result["retrieval_p95_ms"] >= result["retrieval_p50_ms"]
    assert result["queries_per_sec"] > 0
    assert result["insert_per_memory_ms"] > 0
