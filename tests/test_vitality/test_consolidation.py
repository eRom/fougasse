"""Tests for memory consolidation and archival."""

from __future__ import annotations

from fougasse.models import MemoryCreate
from fougasse.storage.database import init_database
from fougasse.storage.memory_store import get_memory, insert_memory
from fougasse.vitality.consolidation import archive_stale_memories, resurrect_memory


def test_archive_stale() -> None:
    db = init_database()
    mem1 = insert_memory(db, MemoryCreate(content="Active memory"))
    mem2 = insert_memory(db, MemoryCreate(content="Stale memory"))

    # Set mem2 vitality below threshold
    db.execute("UPDATE memories SET vitality_score = 0.05 WHERE id = ?", (mem2.id,))
    db.commit()

    result = archive_stale_memories(db, threshold=0.1)
    assert result.archived_count == 1

    # Verify mem2 is archived
    fetched = get_memory(db, mem2.id)
    assert fetched.is_archived is True

    # mem1 should still be active
    fetched1 = get_memory(db, mem1.id)
    assert fetched1.is_archived is False
    db.close()


def test_archive_skips_pinned() -> None:
    db = init_database()
    mem = insert_memory(
        db,
        MemoryCreate(
            content="Pinned memory",
            metadata={"pinned": True},
        ),
    )
    db.execute("UPDATE memories SET vitality_score = 0.01 WHERE id = ?", (mem.id,))
    db.commit()

    result = archive_stale_memories(db, threshold=0.1)
    assert result.archived_count == 0
    assert result.skipped_pinned == 1

    fetched = get_memory(db, mem.id)
    assert fetched.is_archived is False
    db.close()


def test_resurrect_memory() -> None:
    db = init_database()
    mem = insert_memory(db, MemoryCreate(content="Will be archived"))

    # Archive it
    db.execute("UPDATE memories SET is_archived = 1 WHERE id = ?", (mem.id,))
    db.commit()

    # Resurrect
    success = resurrect_memory(db, mem.id, boost_score=1.0)
    assert success is True

    fetched = get_memory(db, mem.id)
    assert fetched.is_archived is False
    assert fetched.vitality_score == 1.0

    # Check access log was created
    log = db.execute("SELECT * FROM access_log WHERE memory_id = ?", (mem.id,)).fetchall()
    assert len(log) == 1
    db.close()


def test_resurrect_nonarchived() -> None:
    db = init_database()
    mem = insert_memory(db, MemoryCreate(content="Active memory"))

    success = resurrect_memory(db, mem.id)
    assert success is False
    db.close()
