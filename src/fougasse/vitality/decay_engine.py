"""ACT-R based vitality decay engine."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime


def compute_vitality(
    db: sqlite3.Connection,
    memory_id: str,
    decay_d: float = 0.5,
    reference_time: datetime | None = None,
) -> float:
    """Compute ACT-R vitality for a single memory.

    vitality = sum(t_i^-d) for each access time t_i (in hours since access).
    Minimum age is 1 hour to avoid division by zero.
    """
    ref = reference_time or datetime.now(UTC)

    rows = db.execute(
        "SELECT accessed_at FROM access_log WHERE memory_id = ? ORDER BY accessed_at DESC",
        (memory_id,),
    ).fetchall()

    if not rows:
        # No access log — use creation time
        created = db.execute(
            "SELECT created_at FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        if not created:
            return 0.0
        try:
            ct = datetime.fromisoformat(created["created_at"].replace("Z", "+00:00"))
            if ct.tzinfo is None:
                ct = ct.replace(tzinfo=UTC)
            hours = max((ref - ct).total_seconds() / 3600.0, 1.0)
            return float(hours ** (-decay_d))
        except (ValueError, TypeError):
            return 0.5

    total = 0.0
    for row in rows:
        try:
            accessed = datetime.fromisoformat(row["accessed_at"].replace("Z", "+00:00"))
            if accessed.tzinfo is None:
                accessed = accessed.replace(tzinfo=UTC)
            hours = max((ref - accessed).total_seconds() / 3600.0, 1.0)
            total += hours ** (-decay_d)
        except (ValueError, TypeError):
            continue

    return total


def update_all_vitalities(
    db: sqlite3.Connection,
    decay_d: float = 0.5,
) -> int:
    """Recalculate vitality scores for all active memories. Returns count updated."""
    rows = db.execute("SELECT id FROM memories WHERE is_archived = 0").fetchall()

    updated = 0
    for row in rows:
        score = compute_vitality(db, row["id"], decay_d=decay_d)
        db.execute(
            "UPDATE memories SET vitality_score = ? WHERE id = ?",
            (score, row["id"]),
        )
        updated += 1

    db.commit()
    return updated
