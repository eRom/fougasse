"""Tests for export/import."""

from __future__ import annotations

from pathlib import Path

from fougasse.io.exporter import export_memories
from fougasse.io.importer import import_memories
from fougasse.models import MemoryCreate, MemoryType
from fougasse.storage.database import init_database
from fougasse.storage.memory_store import count_memories, insert_memory


def test_export_json(tmp_path: Path) -> None:
    db = init_database()
    insert_memory(db, MemoryCreate(content="Memory 1", tags=["python"]))
    insert_memory(db, MemoryCreate(content="Memory 2", type=MemoryType.IDEA))

    output = tmp_path / "export.json"
    data = export_memories(db, output_path=output)

    assert output.exists()
    assert data["count"] == 2
    assert len(data["memories"]) == 2
    assert "vaults" in data
    db.close()


def test_export_import_roundtrip(tmp_path: Path) -> None:
    # Export
    db1 = init_database()
    insert_memory(db1, MemoryCreate(content="Roundtrip test", tags=["test"]))
    insert_memory(db1, MemoryCreate(content="Another memory", type=MemoryType.CODE))

    export_file = tmp_path / "roundtrip.json"
    export_memories(db1, output_path=export_file)
    db1.close()

    # Import into fresh DB
    db2 = init_database()
    result = import_memories(db2, export_file)

    assert result["imported"] == 2
    assert result["skipped"] == 0
    assert count_memories(db2) == 2
    db2.close()


def test_import_with_errors(tmp_path: Path) -> None:
    # Create a file with invalid data
    import json

    bad_data = {
        "memories": [
            {"content": "Valid memory"},
            {"content": ""},  # Empty content — will fail validation
            {"no_content_field": True},  # Missing content
        ]
    }
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(json.dumps(bad_data))

    db = init_database()
    result = import_memories(db, bad_file)
    assert result["imported"] == 1
    assert result["skipped"] == 2
    db.close()
