"""Temporal search channel — boost recent memories."""

from __future__ import annotations

import math
import sqlite3
from datetime import UTC, datetime


def temporal_score(
    db: sqlite3.Connection,
    memory_ids: list[str],
    decay_lambda: float = 0.05,
    reference_time: datetime | None = None,
) -> list[tuple[str, float]]:
    """Compute temporal relevance scores for a list of memory IDs.

    Score = exp(-lambda * age_in_days). Recent memories score higher.
    """
    ref = reference_time or datetime.now(UTC)
    results: list[tuple[str, float]] = []

    if not memory_ids:
        return results

    placeholders = ",".join("?" for _ in memory_ids)
    rows = db.execute(
        f"SELECT id, created_at FROM memories WHERE id IN ({placeholders})",
        memory_ids,
    ).fetchall()

    for row in rows:
        created_str = row["created_at"]
        try:
            # Handle both ISO formats
            if "T" in created_str:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            else:
                created = datetime.fromisoformat(created_str)

            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)

            age_days = (ref - created).total_seconds() / 86400.0
            score = math.exp(-decay_lambda * max(age_days, 0.0))
        except (ValueError, TypeError):
            score = 0.5  # Default for unparseable dates

        results.append((row["id"], score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def filter_by_date_range(
    db: sqlite3.Connection,
    date_from: str | None = None,
    date_to: str | None = None,
    vault_id: str | None = None,
    limit: int = 100,
) -> list[str]:
    """Get memory IDs within a date range."""
    conditions: list[str] = ["is_archived = 0"]
    params: list[object] = []

    if date_from:
        conditions.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= ?")
        params.append(date_to)
    if vault_id:
        conditions.append("vault_id = ?")
        params.append(vault_id)

    where = " AND ".join(conditions)
    params.append(limit)

    rows = db.execute(
        f"SELECT id FROM memories WHERE {where} ORDER BY created_at DESC LIMIT ?",
        params,
    ).fetchall()

    return [row["id"] for row in rows]
