"""CRUD operations for memories in SQLite."""

from __future__ import annotations

import json
import sqlite3
from uuid import uuid4

from fougasse.models import Memory, MemoryCreate, MemoryType, MemoryUpdate, utcnow


def _uuid7() -> str:
    """Generate a UUID v4 (v7 not in stdlib yet, v4 is fine with created_at for ordering)."""
    return str(uuid4())


def _row_to_memory(row: sqlite3.Row, db: sqlite3.Connection) -> Memory:
    """Convert a database row to a Memory model."""
    tags = [r["tag"] for r in db.execute("SELECT tag FROM tags WHERE memory_id = ?", (row["id"],)).fetchall()]
    metadata = json.loads(row["metadata"]) if row["metadata"] else None
    return Memory(
        id=row["id"],
        content=row["content"],
        type=MemoryType(row["type"]),
        tags=tags,
        vault_id=row["vault_id"],
        source_agent=row["source_agent"],
        metadata=metadata,
        vitality_score=row["vitality_score"],
        access_count=row["access_count"],
        is_archived=bool(row["is_archived"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def insert_memory(db: sqlite3.Connection, data: MemoryCreate) -> Memory:
    """Insert a new memory and return it."""
    memory_id = _uuid7()
    now = utcnow().isoformat()
    metadata_json = json.dumps(data.metadata) if data.metadata else None

    with db:
        db.execute(
            """INSERT INTO memories (id, content, type, vault_id, source_agent, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (memory_id, data.content, data.type.value, data.vault_id, data.source_agent, metadata_json, now, now),
        )
        for tag in data.tags:
            db.execute("INSERT INTO tags (memory_id, tag) VALUES (?, ?)", (memory_id, tag))

        # Update FTS index
        tags_str = " ".join(data.tags)
        db.execute(
            "INSERT INTO fts_memories (memory_id, content, tags) VALUES (?, ?, ?)",
            (memory_id, data.content, tags_str),
        )

    row = db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    return _row_to_memory(row, db)


def get_memory(db: sqlite3.Connection, memory_id: str) -> Memory | None:
    """Get a memory by ID, or None if not found."""
    row = db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if row is None:
        return None
    return _row_to_memory(row, db)


def update_memory(db: sqlite3.Connection, memory_id: str, data: MemoryUpdate) -> Memory | None:
    """Update a memory's fields. Returns updated memory or None if not found."""
    existing = db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if existing is None:
        return None

    now = utcnow().isoformat()
    updates: list[str] = ["updated_at = ?"]
    params: list[object] = [now]

    if data.content is not None:
        updates.append("content = ?")
        params.append(data.content)
    if data.type is not None:
        updates.append("type = ?")
        params.append(data.type.value)
    if data.metadata is not None:
        updates.append("metadata = ?")
        params.append(json.dumps(data.metadata))

    params.append(memory_id)

    with db:
        db.execute(f"UPDATE memories SET {', '.join(updates)} WHERE id = ?", params)

        if data.tags is not None:
            db.execute("DELETE FROM tags WHERE memory_id = ?", (memory_id,))
            for tag in data.tags:
                db.execute("INSERT INTO tags (memory_id, tag) VALUES (?, ?)", (memory_id, tag))

        # Update FTS index
        db.execute("DELETE FROM fts_memories WHERE memory_id = ?", (memory_id,))
        updated_row = db.execute("SELECT content FROM memories WHERE id = ?", (memory_id,)).fetchone()
        tag_rows = db.execute("SELECT tag FROM tags WHERE memory_id = ?", (memory_id,)).fetchall()
        tags_str = " ".join(r["tag"] for r in tag_rows)
        db.execute(
            "INSERT INTO fts_memories (memory_id, content, tags) VALUES (?, ?, ?)",
            (memory_id, updated_row["content"], tags_str),
        )

    return get_memory(db, memory_id)


def delete_memory(db: sqlite3.Connection, memory_id: str, hard: bool = False) -> bool:
    """Delete a memory. Soft-delete by default (is_archived=1), hard-delete if specified."""
    existing = db.execute("SELECT id FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if existing is None:
        return False

    with db:
        # Clean FTS index
        db.execute("DELETE FROM fts_memories WHERE memory_id = ?", (memory_id,))

        if hard:
            db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        else:
            db.execute(
                "UPDATE memories SET is_archived = 1, updated_at = ? WHERE id = ?",
                (utcnow().isoformat(), memory_id),
            )
    return True


def list_memories(
    db: sqlite3.Connection,
    vault_id: str | None = None,
    memory_type: MemoryType | None = None,
    tags_filter: list[str] | None = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[Memory]:
    """List memories with optional filters."""
    conditions: list[str] = []
    params: list[object] = []

    if not include_archived:
        conditions.append("m.is_archived = 0")
    if vault_id is not None:
        conditions.append("m.vault_id = ?")
        params.append(vault_id)
    if memory_type is not None:
        conditions.append("m.type = ?")
        params.append(memory_type.value)
    if tags_filter:
        placeholders = ",".join("?" for _ in tags_filter)
        conditions.append(f"m.id IN (SELECT memory_id FROM tags WHERE tag IN ({placeholders}))")
        params.extend(tags_filter)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend([limit, offset])

    rows = db.execute(
        f"SELECT * FROM memories m {where} ORDER BY m.created_at DESC LIMIT ? OFFSET ?",
        params,
    ).fetchall()

    return [_row_to_memory(row, db) for row in rows]


def count_memories(
    db: sqlite3.Connection,
    vault_id: str | None = None,
    include_archived: bool = False,
) -> int:
    """Count memories with optional filters."""
    conditions: list[str] = []
    params: list[object] = []

    if not include_archived:
        conditions.append("is_archived = 0")
    if vault_id is not None:
        conditions.append("vault_id = ?")
        params.append(vault_id)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    row = db.execute(f"SELECT COUNT(*) FROM memories {where}", params).fetchone()
    return row[0] if row else 0
