"""Memory consolidation: archival of stale memories and merge of duplicates."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from fougasse.models import utcnow


@dataclass
class ArchiveResult:
    """Result of archiving stale memories."""

    archived_count: int = 0
    skipped_pinned: int = 0


@dataclass
class MergeCandidate:
    """A pair of memories that could be merged."""

    memory_id_keep: str
    memory_id_archive: str
    similarity: float


def archive_stale_memories(
    db: sqlite3.Connection,
    threshold: float = 0.1,
) -> ArchiveResult:
    """Archive memories with vitality below threshold."""
    result = ArchiveResult()
    now = utcnow().isoformat()

    rows = db.execute(
        "SELECT id, vitality_score FROM memories WHERE is_archived = 0 AND vitality_score < ?",
        (threshold,),
    ).fetchall()

    for row in rows:
        # Check if pinned (metadata contains "pinned": true)
        meta_row = db.execute(
            "SELECT metadata FROM memories WHERE id = ?", (row["id"],)
        ).fetchone()
        if meta_row and meta_row["metadata"]:
            import json
            try:
                meta = json.loads(meta_row["metadata"])
                if meta.get("pinned"):
                    result.skipped_pinned += 1
                    continue
            except (json.JSONDecodeError, TypeError):
                pass

        db.execute(
            "UPDATE memories SET is_archived = 1, updated_at = ? WHERE id = ?",
            (now, row["id"]),
        )
        result.archived_count += 1

    db.commit()
    return result


def find_merge_candidates(
    db: sqlite3.Connection,
    vault_id: str | None = None,
    similarity_threshold: float = 0.9,
    limit: int = 50,
) -> list[MergeCandidate]:
    """Find pairs of memories that are near-duplicates.

    Note: This is a simplified version. Full implementation would use
    vector similarity, but here we use FTS overlap as a heuristic.
    """
    # This would ideally use vector similarity search
    # For now, return empty — full implementation in T30 integration
    return []


def resurrect_memory(
    db: sqlite3.Connection,
    memory_id: str,
    boost_score: float = 1.0,
) -> bool:
    """Resurrect an archived memory by unarchiving and boosting vitality."""
    row = db.execute(
        "SELECT is_archived FROM memories WHERE id = ?", (memory_id,)
    ).fetchone()

    if not row or not row["is_archived"]:
        return False

    now = utcnow().isoformat()
    db.execute(
        "UPDATE memories SET is_archived = 0, vitality_score = ?, updated_at = ? WHERE id = ?",
        (boost_score, now, memory_id),
    )

    # Log the access (resurrection counts as access)
    db.execute(
        "INSERT INTO access_log (memory_id, accessed_at) VALUES (?, ?)",
        (memory_id, now),
    )

    db.commit()
    return True
