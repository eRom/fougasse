"""Tests for ACT-R decay engine."""

from __future__ import annotations

from datetime import UTC, datetime

from fougasse.models import MemoryCreate
from fougasse.storage.database import init_database
from fougasse.storage.memory_store import insert_memory
from fougasse.vitality.decay_engine import compute_vitality, update_all_vitalities


def test_compute_vitality_no_access() -> None:
    db = init_database()
    mem = insert_memory(db, MemoryCreate(content="Test"))
    score = compute_vitality(db, mem.id)
    # Just created, vitality should be positive
    assert score > 0
    db.close()


def test_compute_vitality_with_access() -> None:
    db = init_database()
    mem = insert_memory(db, MemoryCreate(content="Test"))

    # Add some accesses
    now = datetime.now(UTC).isoformat()
    db.execute("INSERT INTO access_log (memory_id, accessed_at) VALUES (?, ?)", (mem.id, now))
    db.commit()

    score = compute_vitality(db, mem.id)
    assert score > 0
    db.close()


def test_compute_vitality_nonexistent() -> None:
    db = init_database()
    score = compute_vitality(db, "fake-id")
    assert score == 0.0
    db.close()


def test_update_all_vitalities() -> None:
    db = init_database()
    for i in range(5):
        insert_memory(db, MemoryCreate(content=f"Memory {i}"))

    updated = update_all_vitalities(db)
    assert updated == 5

    # Verify scores were written
    rows = db.execute("SELECT vitality_score FROM memories WHERE is_archived = 0").fetchall()
    for row in rows:
        assert row["vitality_score"] > 0
    db.close()
