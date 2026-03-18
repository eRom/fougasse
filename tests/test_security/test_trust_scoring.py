"""Tests for Bayesian trust scoring."""

from __future__ import annotations

from fougasse.security.trust_scoring import (
    AgentTrust,
    ensure_trust_table,
    get_agent_trust,
    get_all_trust_scores,
    save_agent_trust,
)
from fougasse.storage.database import init_database


def test_initial_trust() -> None:
    trust = AgentTrust(agent_id="claude-code")
    assert trust.score == 0.5  # Uniform prior
    assert trust.is_trusted is True


def test_positive_feedback() -> None:
    trust = AgentTrust(agent_id="claude-code")
    for _ in range(50):
        trust.positive_feedback()
    assert trust.score > 0.5


def test_negative_feedback() -> None:
    trust = AgentTrust(agent_id="malicious-agent")
    for _ in range(50):
        trust.negative_feedback()
    assert trust.score < 0.3
    assert trust.is_trusted is False


def test_asymmetric_feedback() -> None:
    trust = AgentTrust(agent_id="test")
    trust.positive_feedback(0.02)
    trust.negative_feedback(0.03)
    # After equal pos+neg, score should be slightly below 0.5
    assert trust.score < 0.5


def test_persistence() -> None:
    db = init_database()
    ensure_trust_table(db)

    trust = AgentTrust(agent_id="claude-code", alpha=2.0, beta=1.5)
    save_agent_trust(db, trust)

    loaded = get_agent_trust(db, "claude-code")
    assert loaded.alpha == 2.0
    assert loaded.beta == 1.5
    db.close()


def test_get_all_trust_scores() -> None:
    db = init_database()
    ensure_trust_table(db)

    save_agent_trust(db, AgentTrust("agent-a", alpha=3.0, beta=1.0))
    save_agent_trust(db, AgentTrust("agent-b", alpha=1.0, beta=5.0))

    scores = get_all_trust_scores(db)
    assert len(scores) == 2
    ids = {s["agent_id"] for s in scores}
    assert "agent-a" in ids
    assert "agent-b" in ids
    db.close()
