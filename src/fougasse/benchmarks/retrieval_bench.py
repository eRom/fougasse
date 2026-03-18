"""Built-in benchmarks for measuring retrieval performance."""

from __future__ import annotations

import random
import time

from fougasse.models import MemoryCreate, SearchQuery
from fougasse.retrieval.hybrid_search import hybrid_search
from fougasse.storage.database import init_database
from fougasse.storage.fts_store import index_memory
from fougasse.storage.memory_store import insert_memory
from fougasse.storage.vector_store import ensure_vec_table, insert_vector


def _random_content(word_count: int = 20) -> str:
    words = [
        "python",
        "rust",
        "docker",
        "api",
        "database",
        "memory",
        "graph",
        "search",
        "deploy",
        "test",
        "build",
        "config",
        "server",
        "client",
        "model",
        "train",
        "data",
        "query",
        "index",
        "cache",
        "async",
        "function",
        "class",
        "module",
        "package",
        "framework",
        "library",
    ]
    return " ".join(random.choices(words, k=word_count))


def _random_vector(dim: int) -> list[float]:
    vec = [random.gauss(0, 1) for _ in range(dim)]
    mag = sum(v * v for v in vec) ** 0.5
    return [v / mag for v in vec]


def run_benchmark(
    count: int = 1000,
    dim: int = 4,  # Small dim for benchmark speed
    queries: int = 100,
) -> dict:
    """Run retrieval benchmark with synthetic data.

    Uses small embedding dimensions for speed. Real-world uses 768.
    """
    db = init_database()
    ensure_vec_table(db, dim=dim)

    # Phase 1: Insertion
    t0 = time.perf_counter()
    memory_ids = []
    for _ in range(count):
        content = _random_content()
        tags = random.sample(["python", "rust", "docker", "ml", "web", "api", "db"], k=2)
        mem = insert_memory(db, MemoryCreate(content=content, tags=tags))
        vec = _random_vector(dim)
        insert_vector(db, mem.id, "default", vec)
        index_memory(db, mem.id, content, tags)
        memory_ids.append(mem.id)

    insert_time = time.perf_counter() - t0

    # Phase 2: Retrieval
    latencies = []
    mock_embed = lambda text: _random_vector(dim)

    for _ in range(queries):
        query_text = _random_content(word_count=5)
        t1 = time.perf_counter()
        hybrid_search(
            db,
            SearchQuery(query=query_text, limit=10),
            embed_fn=mock_embed,
        )
        latencies.append((time.perf_counter() - t1) * 1000)

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    db.close()

    return {
        "memories": count,
        "queries": queries,
        "embedding_dim": dim,
        "insert_total_ms": round(insert_time * 1000, 1),
        "insert_per_memory_ms": round(insert_time * 1000 / count, 2),
        "retrieval_p50_ms": round(p50, 2),
        "retrieval_p95_ms": round(p95, 2),
        "retrieval_p99_ms": round(p99, 2),
        "queries_per_sec": round(queries / sum(latencies) * 1000, 1),
    }
