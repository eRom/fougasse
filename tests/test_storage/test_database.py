"""Tests for database module."""

from __future__ import annotations

from pathlib import Path

from fougasse.storage.database import (
    get_connection,
    get_current_version,
    init_database,
    run_migrations,
)


def test_get_connection_memory() -> None:
    db = get_connection(":memory:")
    # Check WAL mode
    mode = db.execute("PRAGMA journal_mode").fetchone()[0]
    # In-memory DB can't use WAL, falls back to 'memory'
    assert mode in ("wal", "memory")

    # Check foreign keys enabled
    fk = db.execute("PRAGMA foreign_keys").fetchone()[0]
    assert fk == 1

    # Check sqlite-vec loaded
    ver = db.execute("SELECT vec_version()").fetchone()[0]
    assert ver.startswith("v")
    db.close()


def test_get_connection_file(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    db = get_connection(db_path)
    mode = db.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"
    db.close()
    assert db_path.exists()


def test_init_database_memory() -> None:
    db = init_database()
    # Check tables exist
    tables = {
        r[0]
        for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "memories" in tables
    assert "vaults" in tables
    assert "tags" in tables
    assert "access_log" in tables
    assert "graph_nodes" in tables
    assert "graph_edges" in tables
    assert "schema_version" in tables

    # Check default vault
    vault = db.execute("SELECT * FROM vaults WHERE id = 'default'").fetchone()
    assert vault is not None
    assert vault["name"] == "default"

    # Check schema version
    ver = get_current_version(db)
    assert ver >= 1
    db.close()


def test_migrations_idempotent() -> None:
    db = init_database()
    ver1 = get_current_version(db)
    # Running migrations again should apply 0
    applied = run_migrations(db)
    assert applied == 0
    ver2 = get_current_version(db)
    assert ver1 == ver2
    db.close()


def test_init_database_file(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    db = init_database(db_path)
    assert db_path.exists()
    ver = get_current_version(db)
    assert ver >= 1
    db.close()
