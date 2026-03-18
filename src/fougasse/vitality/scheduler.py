"""Periodic scheduler for vitality updates and consolidation."""

from __future__ import annotations

import asyncio
import logging
import sqlite3

from fougasse.vitality.consolidation import archive_stale_memories
from fougasse.vitality.decay_engine import update_all_vitalities

logger = logging.getLogger("fougasse.scheduler")


class VitalityScheduler:
    """Background task that periodically updates vitality scores and archives stale memories."""

    def __init__(
        self,
        db: sqlite3.Connection,
        interval_hours: float = 6.0,
        decay_d: float = 0.5,
        archive_threshold: float = 0.1,
    ):
        self.db = db
        self.interval_seconds = interval_hours * 3600
        self.decay_d = decay_d
        self.archive_threshold = archive_threshold
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the periodic scheduler."""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "Vitality scheduler started (interval: %.1fh, decay_d: %.2f, threshold: %.2f)",
            self.interval_seconds / 3600,
            self.decay_d,
            self.archive_threshold,
        )

    async def stop(self) -> None:
        """Stop the scheduler gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Vitality scheduler stopped.")

    async def _run_loop(self) -> None:
        """Main loop: sleep then process."""
        while self._running:
            try:
                await asyncio.sleep(self.interval_seconds)
                self.run_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in vitality scheduler cycle")

    def run_cycle(self) -> dict:
        """Execute one cycle: update vitalities + archive stale."""
        updated = update_all_vitalities(self.db, decay_d=self.decay_d)
        archive_result = archive_stale_memories(self.db, threshold=self.archive_threshold)

        result = {
            "vitalities_updated": updated,
            "archived": archive_result.archived_count,
            "skipped_pinned": archive_result.skipped_pinned,
        }
        logger.info("Vitality cycle: %s", result)
        return result
