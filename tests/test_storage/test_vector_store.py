"""Tests for vector store operations."""

from __future__ import annotations

import pytest

from fougasse.storage.database import init_database
from fougasse.storage.vector_store import delete_vector, ensure_vec_table, insert_vector, search_knn


@pytest.fixture
def db():
    conn = init_database()
    ensure_vec_table(conn, dim=4)
    yield conn
    conn.close()


def test_insert_and_search(db) -> None:
    insert_vector(db, "mem-1", "default", [1.0, 0.0, 0.0, 0.0])
    insert_vector(db, "mem-2", "default", [0.0, 1.0, 0.0, 0.0])
    insert_vector(db, "mem-3", "default", [1.0, 0.1, 0.0, 0.0])

    results = search_knn(db, [1.0, 0.0, 0.0, 0.0], k=2)
    assert len(results) == 2
    assert results[0][0] == "mem-1"  # Closest
    assert results[0][1] < results[1][1]  # Ordered by distance


def test_search_empty(db) -> None:
    results = search_knn(db, [1.0, 0.0, 0.0, 0.0], k=5)
    assert results == []


def test_vault_filtering(db) -> None:
    insert_vector(db, "mem-1", "vault-a", [1.0, 0.0, 0.0, 0.0])
    insert_vector(db, "mem-2", "vault-b", [1.0, 0.1, 0.0, 0.0])

    results = search_knn(db, [1.0, 0.0, 0.0, 0.0], k=5, vault_id="vault-a")
    assert len(results) == 1
    assert results[0][0] == "mem-1"


def test_archived_filtering(db) -> None:
    insert_vector(db, "mem-1", "default", [1.0, 0.0, 0.0, 0.0], is_archived=0)
    insert_vector(db, "mem-2", "default", [1.0, 0.1, 0.0, 0.0], is_archived=1)

    results = search_knn(db, [1.0, 0.0, 0.0, 0.0], k=5, include_archived=False)
    assert len(results) == 1
    assert results[0][0] == "mem-1"

    results_all = search_knn(db, [1.0, 0.0, 0.0, 0.0], k=5, include_archived=True)
    assert len(results_all) == 2


def test_delete_vector(db) -> None:
    insert_vector(db, "mem-1", "default", [1.0, 0.0, 0.0, 0.0])
    delete_vector(db, "mem-1")
    results = search_knn(db, [1.0, 0.0, 0.0, 0.0], k=5)
    assert results == []


def test_upsert_vector(db) -> None:
    insert_vector(db, "mem-1", "default", [1.0, 0.0, 0.0, 0.0])
    insert_vector(db, "mem-1", "default", [0.0, 1.0, 0.0, 0.0])  # Replace

    results = search_knn(db, [0.0, 1.0, 0.0, 0.0], k=1)
    assert len(results) == 1
    assert results[0][0] == "mem-1"
    assert results[0][1] < 0.01  # Should be very close
