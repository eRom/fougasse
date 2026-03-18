"""sqlite-vec vector storage and KNN search operations."""

from __future__ import annotations

import sqlite3

from fougasse.embeddings import serialize_vector


def ensure_vec_table(db: sqlite3.Connection, dim: int = 768) -> None:
    """Create the vec0 virtual table if it doesn't exist."""
    db.execute(
        f"""CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories USING vec0(
            memory_id TEXT,
            vault_id TEXT,
            is_archived INTEGER,
            embedding float[{dim}]
        )"""
    )


def insert_vector(
    db: sqlite3.Connection,
    memory_id: str,
    vault_id: str,
    embedding: list[float],
    is_archived: int = 0,
) -> None:
    """Insert or replace a vector for a memory."""
    vec_bytes = serialize_vector(embedding)
    # Delete existing if any (upsert)
    db.execute("DELETE FROM vec_memories WHERE memory_id = ?", (memory_id,))
    db.execute(
        "INSERT INTO vec_memories (memory_id, vault_id, is_archived, embedding) VALUES (?, ?, ?, ?)",
        (memory_id, vault_id, is_archived, vec_bytes),
    )


def delete_vector(db: sqlite3.Connection, memory_id: str) -> None:
    """Delete vector for a memory."""
    db.execute("DELETE FROM vec_memories WHERE memory_id = ?", (memory_id,))


def search_knn(
    db: sqlite3.Connection,
    query_embedding: list[float],
    k: int = 10,
    vault_id: str | None = None,
    include_archived: bool = False,
) -> list[tuple[str, float]]:
    """KNN search returning (memory_id, distance) pairs."""
    vec_bytes = serialize_vector(query_embedding)

    conditions = ["embedding MATCH ?", "k = ?"]
    params: list[object] = [vec_bytes, k]

    if vault_id is not None:
        conditions.append("vault_id = ?")
        params.append(vault_id)
    if not include_archived:
        conditions.append("is_archived = 0")

    where = " AND ".join(conditions)
    query = f"""
        SELECT memory_id, distance
        FROM vec_memories
        WHERE {where}
        ORDER BY distance
    """

    rows = db.execute(query, params).fetchall()
    return [(row[0], row[1]) for row in rows]
