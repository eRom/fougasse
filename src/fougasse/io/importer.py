"""Import memories from JSON format."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fougasse.models import MemoryCreate, MemoryType
from fougasse.storage.memory_store import insert_memory


def import_memories(
    db: sqlite3.Connection,
    input_path: Path,
    re_embed: bool = True,
) -> dict:
    """Import memories from a JSON export file.

    Returns summary of import results.
    """
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    imported = 0
    skipped = 0
    errors: list[str] = []

    # Import vaults first
    for vault_data in data.get("vaults", []):
        try:
            db.execute(
                "INSERT OR IGNORE INTO vaults (id, name, description, created_at) VALUES (?, ?, ?, ?)",
                (vault_data["id"], vault_data["name"], vault_data.get("description"), vault_data.get("created_at", "")),
            )
        except Exception:
            pass

    # Import memories
    for mem_data in data.get("memories", []):
        try:
            mem_type = MemoryType(mem_data.get("type", "text"))
            create = MemoryCreate(
                content=mem_data["content"],
                type=mem_type,
                tags=mem_data.get("tags", []),
                vault_id=mem_data.get("vault_id", "default"),
                source_agent=mem_data.get("source_agent"),
                metadata=mem_data.get("metadata"),
            )
            insert_memory(db, create)
            imported += 1
        except Exception as e:
            errors.append(f"Skipped: {str(e)[:100]}")
            skipped += 1

    db.commit()

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10],  # First 10 errors
        "source_version": data.get("fougasse_version", "unknown"),
    }
