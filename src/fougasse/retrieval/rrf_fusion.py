"""Reciprocal Rank Fusion (RRF) for combining multiple ranked lists."""

from __future__ import annotations


def rrf_fuse(
    ranked_lists: list[list[tuple[str, float]]],
    k: int = 60,
    weights: list[float] | None = None,
) -> list[tuple[str, float]]:
    """Fuse multiple ranked lists using Reciprocal Rank Fusion.

    Each ranked list is a list of (item_id, score) tuples, ordered by relevance.
    Returns a fused list of (item_id, combined_score), sorted by combined score descending.
    """
    if not ranked_lists:
        return []

    w = weights or [1.0] * len(ranked_lists)
    scores: dict[str, float] = {}

    for rank_list, weight in zip(ranked_lists, w):
        for rank_pos, (item_id, _score) in enumerate(rank_list):
            rrf_score = weight / (k + rank_pos + 1)
            scores[item_id] = scores.get(item_id, 0.0) + rrf_score

    # Sort by combined score descending
    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return fused
