"""Tests for temporal search channel."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fougasse.models import MemoryCreate
from fougasse.retrieval.temporal_search import filter_by_date_range, temporal_score
from fougasse.storage.database import init_database
from fougasse.storage.memory_store import insert_memory


def test_temporal_score_recent_higher() -> None:
    db = init_database()
    mem1 = insert_memory(db, MemoryCreate(content="Recent memory"))
    mem2 = insert_memory(db, MemoryCreate(content="Another memory"))

    scores = temporal_score(db, [mem1.id, mem2.id])
    # Both created now, should have similar high scores
    for _, score in scores:
        assert score > 0.9
    db.close()


def test_temporal_score_empty() -> None:
    db = init_database()
    assert temporal_score(db, []) == []
    db.close()


def test_filter_by_date_range() -> None:
    db = init_database()
    insert_memory(db, MemoryCreate(content="Memory 1"))
    insert_memory(db, MemoryCreate(content="Memory 2"))

    now = datetime.now(UTC)
    ids = filter_by_date_range(
        db,
        date_from=(now - timedelta(hours=1)).isoformat(),
        date_to=(now + timedelta(hours=1)).isoformat(),
    )
    assert len(ids) == 2
    db.close()


def test_filter_by_date_range_vault() -> None:
    db = init_database()
    db.execute("INSERT INTO vaults (id, name) VALUES ('work', 'work')")
    insert_memory(db, MemoryCreate(content="Default vault"))
    insert_memory(db, MemoryCreate(content="Work vault", vault_id="work"))

    ids = filter_by_date_range(db, vault_id="work")
    assert len(ids) == 1
    db.close()
