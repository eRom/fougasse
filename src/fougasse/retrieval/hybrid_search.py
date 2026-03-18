"""Hybrid search orchestrator combining multiple retrieval channels."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable

from fougasse.embeddings import encode
from fougasse.graph.knowledge_graph import KnowledgeGraph
from fougasse.models import SearchQuery, SearchResult, SearchResultItem
from fougasse.retrieval.graph_search import spreading_activation
from fougasse.retrieval.rrf_fusion import rrf_fuse
from fougasse.retrieval.temporal_search import temporal_score
from fougasse.storage.fts_store import search_bm25
from fougasse.storage.memory_store import get_memory
from fougasse.storage.vector_store import search_knn


def hybrid_search(
    db: sqlite3.Connection,
    query: SearchQuery,
    embed_fn: Callable[[str], list[float]] | None = None,
    rrf_k: int = 60,
    knowledge_graph: KnowledgeGraph | None = None,
    channel_weights: list[float] | None = None,
) -> SearchResult:
    """Execute hybrid search combining up to 4 channels.

    Channels:
    1. Semantic (vector KNN via sqlite-vec)
    2. BM25 (FTS5 full-text)
    3. Graph (spreading activation) — if knowledge_graph provided
    4. Temporal (recency boost) — always active
    """
    start = time.perf_counter()
    fetch_k = query.limit * 3

    # Generate query embedding
    query_embedding = embed_fn(query.query) if embed_fn else encode(query.query)

    # Channel 1: Vector KNN search
    vec_results = search_knn(
        db,
        query_embedding,
        k=fetch_k,
        vault_id=query.vault_id,
        include_archived=query.include_archived,
    )

    # Channel 2: FTS5 BM25 search
    fts_results = search_bm25(db, query.query, limit=fetch_k)
    if query.vault_id:
        fts_results = [
            (mid, rank) for mid, rank in fts_results
            if _memory_in_vault(db, mid, query.vault_id)
        ]

    ranked_lists: list[list[tuple[str, float]]] = [vec_results, fts_results]
    weights = list(channel_weights) if channel_weights else [1.0, 1.0]

    # Channel 3: Graph spreading activation (if available)
    if knowledge_graph and knowledge_graph.node_count > 0:
        seed_ids = [mid for mid, _ in vec_results[:3]]  # Top-3 vec as seeds
        graph_results = spreading_activation(
            knowledge_graph, seed_ids, max_hops=3, max_results=fetch_k
        )
        ranked_lists.append(graph_results)
        weights.append(weights[0] if len(weights) <= 2 else weights[2] if len(weights) > 2 else 1.0)
    else:
        weights = weights[:2]

    # Channel 4: Temporal recency
    all_candidate_ids = list({mid for rl in ranked_lists for mid, _ in rl})
    if all_candidate_ids:
        temp_results = temporal_score(db, all_candidate_ids)
        ranked_lists.append(temp_results)
        weights.append(0.5)  # Lower weight for temporal

    # RRF Fusion
    fused = rrf_fuse(ranked_lists, k=rrf_k, weights=weights)

    # Build results
    results: list[SearchResultItem] = []
    seen: set[str] = set()
    vec_ids = {mid for mid, _ in vec_results}
    fts_ids = {mid for mid, _ in fts_results}

    for memory_id, score in fused:
        if memory_id in seen:
            continue
        if query.min_score is not None and score < query.min_score:
            continue

        mem = get_memory(db, memory_id)
        if mem is None:
            continue
        if mem.is_archived and not query.include_archived:
            continue
        if query.type_filter and mem.type != query.type_filter:
            continue
        if query.tags_filter and not any(t in mem.tags for t in query.tags_filter):
            continue

        sources = []
        if memory_id in vec_ids:
            sources.append("semantic")
        if memory_id in fts_ids:
            sources.append("bm25")
        if knowledge_graph and knowledge_graph.has_node(memory_id):
            sources.append("graph")
        sources.append("temporal")

        results.append(SearchResultItem(memory=mem, score=score, match_sources=sources))
        seen.add(memory_id)

        if len(results) >= query.limit:
            break

    elapsed = (time.perf_counter() - start) * 1000

    return SearchResult(
        results=results,
        total_count=len(results),
        query=query.query,
        search_time_ms=round(elapsed, 2),
    )


def _memory_in_vault(db: sqlite3.Connection, memory_id: str, vault_id: str) -> bool:
    """Check if a memory belongs to a vault."""
    row = db.execute(
        "SELECT 1 FROM memories WHERE id = ? AND vault_id = ?",
        (memory_id, vault_id),
    ).fetchone()
    return row is not None
