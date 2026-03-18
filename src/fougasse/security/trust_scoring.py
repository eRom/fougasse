"""Bayesian trust scoring per source agent (Beta-Binomial model)."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class AgentTrust:
    """Trust state for an agent."""

    agent_id: str
    alpha: float = 1.0  # Positive evidence
    beta: float = 1.0  # Negative evidence

    @property
    def score(self) -> float:
        """Expected trust score: alpha / (alpha + beta)."""
        return self.alpha / (self.alpha + self.beta)

    @property
    def is_trusted(self) -> bool:
        return self.score >= 0.3

    def positive_feedback(self, magnitude: float = 0.02) -> None:
        """Memory was useful — small trust increase (hard to earn)."""
        self.alpha += magnitude

    def negative_feedback(self, magnitude: float = 0.03) -> None:
        """Memory was incorrect — larger trust decrease (easy to lose)."""
        self.beta += magnitude


def get_agent_trust(db: sqlite3.Connection, agent_id: str) -> AgentTrust:
    """Load or initialize trust for an agent."""
    row = db.execute(
        "SELECT alpha, beta FROM agent_trust WHERE agent_id = ?",
        (agent_id,),
    ).fetchone()

    if row:
        return AgentTrust(agent_id=agent_id, alpha=row[0], beta=row[1])
    return AgentTrust(agent_id=agent_id)


def save_agent_trust(db: sqlite3.Connection, trust: AgentTrust) -> None:
    """Persist agent trust scores."""
    db.execute(
        """INSERT OR REPLACE INTO agent_trust (agent_id, alpha, beta)
           VALUES (?, ?, ?)""",
        (trust.agent_id, trust.alpha, trust.beta),
    )
    db.commit()


def ensure_trust_table(db: sqlite3.Connection) -> None:
    """Create the agent_trust table if it doesn't exist."""
    db.execute(
        """CREATE TABLE IF NOT EXISTS agent_trust (
            agent_id TEXT PRIMARY KEY,
            alpha REAL NOT NULL DEFAULT 1.0,
            beta REAL NOT NULL DEFAULT 1.0
        )"""
    )
    db.commit()


def get_all_trust_scores(db: sqlite3.Connection) -> list[dict[str, object]]:
    """Get trust scores for all known agents."""
    ensure_trust_table(db)
    rows = db.execute("SELECT agent_id, alpha, beta FROM agent_trust").fetchall()
    return [
        {
            "agent_id": row[0],
            "alpha": row[1],
            "beta": row[2],
            "score": row[1] / (row[1] + row[2]),
            "trusted": (row[1] / (row[1] + row[2])) >= 0.3,
        }
        for row in rows
    ]
