"""Tests for memory store CRUD operations."""

from __future__ import annotations

import pytest

from fougasse.models import MemoryCreate, MemoryType, MemoryUpdate
from fougasse.storage.database import init_database
from fougasse.storage.memory_store import (
    count_memories,
    delete_memory,
    get_memory,
    insert_memory,
    list_memories,
    update_memory,
)


@pytest.fixture
def db():
    conn = init_database()
    yield conn
    conn.close()


def test_insert_and_get(db) -> None:
    data = MemoryCreate(content="Hello world", type=MemoryType.TEXT, tags=["test", "hello"])
    mem = insert_memory(db, data)
    assert mem.id is not None
    assert mem.content == "Hello world"
    assert mem.type == MemoryType.TEXT
    assert sorted(mem.tags) == ["hello", "test"]
    assert mem.vault_id == "default"
    assert mem.is_archived is False
    assert mem.vitality_score == 1.0

    fetched = get_memory(db, mem.id)
    assert fetched is not None
    assert fetched.id == mem.id
    assert fetched.content == mem.content


def test_get_nonexistent(db) -> None:
    assert get_memory(db, "nonexistent-id") is None


def test_insert_with_metadata(db) -> None:
    data = MemoryCreate(
        content="Task with meta",
        type=MemoryType.TASK,
        metadata={"priority": "high", "due": "2026-04-01"},
    )
    mem = insert_memory(db, data)
    assert mem.metadata == {"priority": "high", "due": "2026-04-01"}


def test_insert_with_source_agent(db) -> None:
    data = MemoryCreate(content="From Claude", source_agent="claude-code")
    mem = insert_memory(db, data)
    assert mem.source_agent == "claude-code"


def test_update_content(db) -> None:
    data = MemoryCreate(content="Original", tags=["v1"])
    mem = insert_memory(db, data)

    updated = update_memory(db, mem.id, MemoryUpdate(content="Updated"))
    assert updated is not None
    assert updated.content == "Updated"
    assert updated.tags == ["v1"]  # Tags unchanged


def test_update_tags(db) -> None:
    data = MemoryCreate(content="Test", tags=["old"])
    mem = insert_memory(db, data)

    updated = update_memory(db, mem.id, MemoryUpdate(tags=["new-tag-1", "new-tag-2"]))
    assert updated is not None
    assert sorted(updated.tags) == ["new-tag-1", "new-tag-2"]


def test_update_nonexistent(db) -> None:
    result = update_memory(db, "fake-id", MemoryUpdate(content="nope"))
    assert result is None


def test_soft_delete(db) -> None:
    data = MemoryCreate(content="To delete")
    mem = insert_memory(db, data)

    assert delete_memory(db, mem.id) is True
    fetched = get_memory(db, mem.id)
    assert fetched is not None
    assert fetched.is_archived is True


def test_hard_delete(db) -> None:
    data = MemoryCreate(content="To hard delete")
    mem = insert_memory(db, data)

    assert delete_memory(db, mem.id, hard=True) is True
    assert get_memory(db, mem.id) is None


def test_delete_nonexistent(db) -> None:
    assert delete_memory(db, "fake-id") is False


def test_list_memories(db) -> None:
    for i in range(5):
        insert_memory(db, MemoryCreate(content=f"Memory {i}"))

    memories = list_memories(db)
    assert len(memories) == 5


def test_list_memories_filter_vault(db) -> None:
    # Create another vault
    db.execute("INSERT INTO vaults (id, name) VALUES ('work', 'work')")
    insert_memory(db, MemoryCreate(content="Default vault"))
    insert_memory(db, MemoryCreate(content="Work vault", vault_id="work"))

    default_mems = list_memories(db, vault_id="default")
    assert len(default_mems) == 1
    work_mems = list_memories(db, vault_id="work")
    assert len(work_mems) == 1


def test_list_memories_filter_type(db) -> None:
    insert_memory(db, MemoryCreate(content="A task", type=MemoryType.TASK))
    insert_memory(db, MemoryCreate(content="An idea", type=MemoryType.IDEA))

    tasks = list_memories(db, memory_type=MemoryType.TASK)
    assert len(tasks) == 1
    assert tasks[0].type == MemoryType.TASK


def test_list_memories_filter_tags(db) -> None:
    insert_memory(db, MemoryCreate(content="Python stuff", tags=["python"]))
    insert_memory(db, MemoryCreate(content="Rust stuff", tags=["rust"]))
    insert_memory(db, MemoryCreate(content="Both", tags=["python", "rust"]))

    python_mems = list_memories(db, tags_filter=["python"])
    assert len(python_mems) == 2


def test_list_memories_excludes_archived(db) -> None:
    mem = insert_memory(db, MemoryCreate(content="Will archive"))
    insert_memory(db, MemoryCreate(content="Will keep"))
    delete_memory(db, mem.id)  # soft-delete

    active = list_memories(db, include_archived=False)
    assert len(active) == 1
    all_mems = list_memories(db, include_archived=True)
    assert len(all_mems) == 2


def test_count_memories(db) -> None:
    for i in range(3):
        insert_memory(db, MemoryCreate(content=f"Mem {i}"))
    assert count_memories(db) == 3

    # Archive one
    mems = list_memories(db)
    delete_memory(db, mems[0].id)
    assert count_memories(db) == 2
    assert count_memories(db, include_archived=True) == 3


def test_list_memories_pagination(db) -> None:
    for i in range(10):
        insert_memory(db, MemoryCreate(content=f"Mem {i}"))

    page1 = list_memories(db, limit=3, offset=0)
    page2 = list_memories(db, limit=3, offset=3)
    assert len(page1) == 3
    assert len(page2) == 3
    assert page1[0].id != page2[0].id
