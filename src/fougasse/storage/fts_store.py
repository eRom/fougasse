"""FTS5 full-text search operations."""

from __future__ import annotations

import sqlite3


def index_memory(db: sqlite3.Connection, memory_id: str, content: str, tags: list[str]) -> None:
    """Index or re-index a memory in FTS5."""
    tags_str = " ".join(tags)
    # Remove old entry if exists
    db.execute("DELETE FROM fts_memories WHERE memory_id = ?", (memory_id,))
    # Insert new
    db.execute(
        "INSERT INTO fts_memories (memory_id, content, tags) VALUES (?, ?, ?)",
        (memory_id, content, tags_str),
    )


def remove_from_index(db: sqlite3.Connection, memory_id: str) -> None:
    """Remove a memory from the FTS5 index."""
    db.execute("DELETE FROM fts_memories WHERE memory_id = ?", (memory_id,))


def search_bm25(
    db: sqlite3.Connection,
    query: str,
    limit: int = 10,
) -> list[tuple[str, float]]:
    """BM25 full-text search returning (memory_id, rank) pairs. Lower rank = more relevant."""
    # Sanitize for FTS5: remove special operators, keep only words
    import re

    words = re.findall(r"\w+", query, re.UNICODE)
    if not words:
        return []
    safe_query = " ".join(words)

    try:
        rows = db.execute(
            """SELECT memory_id, rank
               FROM fts_memories
               WHERE fts_memories MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (safe_query, limit),
        ).fetchall()
    except sqlite3.OperationalError:
        return []

    return [(row[0], row[1]) for row in rows]
