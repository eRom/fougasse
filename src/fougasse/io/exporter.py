"""Export memories to JSON format."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fougasse import __version__
from fougasse.storage.memory_store import list_memories


def export_memories(
    db: sqlite3.Connection,
    output_path: Path | None = None,
    vault_id: str | None = None,
    include_graph: bool = True,
) -> dict[str, object]:
    """Export memories (and optionally graph) to a JSON-serializable dict."""
    memories = list_memories(db, vault_id=vault_id, include_archived=True, limit=999999)

    data: dict[str, object] = {
        "fougasse_version": __version__,
        "export_format": "1.0",
        "count": len(memories),
        "vault_filter": vault_id,
        "memories": [m.model_dump(mode="json") for m in memories],
    }

    if include_graph:
        nodes = db.execute("SELECT * FROM graph_nodes").fetchall()
        edges = db.execute("SELECT * FROM graph_edges").fetchall()
        data["graph"] = {
            "nodes": [dict(n) for n in nodes],
            "edges": [dict(e) for e in edges],
        }

    # Vaults
    vaults = db.execute("SELECT * FROM vaults").fetchall()
    data["vaults"] = [dict(v) for v in vaults]

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    return data
