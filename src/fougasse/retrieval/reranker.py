"""Cross-encoder reranking for improved precision."""

from __future__ import annotations

from typing import Any

from fougasse.models import SearchResultItem

_reranker: Any = None
_reranker_name: str = ""


def load_reranker(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> Any:
    """Load cross-encoder model (lazy singleton)."""
    global _reranker, _reranker_name

    if _reranker is not None and _reranker_name == model_name:
        return _reranker

    from sentence_transformers import CrossEncoder

    _reranker = CrossEncoder(model_name)
    _reranker_name = model_name
    return _reranker


def rerank(
    query: str,
    results: list[SearchResultItem],
    top_k: int = 20,
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
) -> list[SearchResultItem]:
    """Rerank search results using a cross-encoder.

    Takes the top_k results from RRF fusion and re-scores them
    using query-document pair scoring. Returns reranked list.
    """
    if not results:
        return results

    candidates = results[:top_k]
    model = load_reranker(model_name)

    # Create query-document pairs
    pairs = [(query, r.memory.content) for r in candidates]

    # Score all pairs
    scores = model.predict(pairs)

    # Update scores and sort
    reranked = []
    for item, ce_score in zip(candidates, scores):
        reranked.append(
            SearchResultItem(
                memory=item.memory,
                score=float(ce_score),
                match_sources=item.match_sources + ["reranked"],
            )
        )

    reranked.sort(key=lambda x: x.score, reverse=True)

    # Append remaining items (beyond top_k) unchanged
    if len(results) > top_k:
        reranked.extend(results[top_k:])

    return reranked
