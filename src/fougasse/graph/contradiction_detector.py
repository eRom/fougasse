"""Semantic contradiction detection at write time."""

from __future__ import annotations

import re
from dataclasses import dataclass

from fougasse.graph.knowledge_graph import KnowledgeGraph

# Negation patterns (French + English)
_NEGATION_PATTERNS = [
    r"\bn['\u2019]est\s+pas\b",
    r"\bne\b.*\bpas\b",
    r"\bplus\b",
    r"\bannule\b",
    r"\bremplace\b",
    r"\bcontrairement\b",
    r"\ben fait\b",
    r"\bnot\b",
    r"\bno longer\b",
    r"\bcancel\b",
    r"\breplace\b",
    r"\bactually\b",
    r"\binstead\b",
    r"\bwrong\b",
    r"\bincorrect\b",
    r"\bchanged\b.*\bto\b",
    r"\bno\b",
    r"\bnever\b",
]


@dataclass
class ContradictionResult:
    """Result of contradiction check."""

    has_contradiction: bool
    conflicting_memory_id: str | None = None
    similarity: float = 0.0
    relation_type: str = "conflicts_with"  # supersedes or conflicts_with
    reason: str = ""


def check_negation(text1: str, text2: str) -> bool:
    """Check if either text contains negation patterns relative to the other."""
    combined = f"{text1} {text2}".lower()
    for pattern in _NEGATION_PATTERNS:
        if re.search(pattern, combined):
            return True
    return False


def detect_contradiction(
    new_content: str,
    similar_memories: list[tuple[str, float, str]],
    similarity_threshold: float = 0.85,
) -> ContradictionResult:
    """Detect if new content contradicts existing memories.

    Args:
        new_content: The new memory content.
        similar_memories: List of (memory_id, similarity_score, content) tuples.
        similarity_threshold: Minimum similarity to consider a potential contradiction.

    Returns:
        ContradictionResult with detection details.
    """
    for mem_id, similarity, existing_content in similar_memories:
        if similarity < similarity_threshold:
            continue

        if check_negation(new_content, existing_content):
            # High similarity + negation = likely supersedes
            return ContradictionResult(
                has_contradiction=True,
                conflicting_memory_id=mem_id,
                similarity=similarity,
                relation_type="supersedes",
                reason=f"High similarity ({similarity:.2f}) with negation pattern detected.",
            )

        # Very high similarity without negation could be a conflict
        if similarity > 0.95:
            return ContradictionResult(
                has_contradiction=True,
                conflicting_memory_id=mem_id,
                similarity=similarity,
                relation_type="conflicts_with",
                reason=f"Very high similarity ({similarity:.2f}) — possible duplicate or conflict.",
            )

    return ContradictionResult(has_contradiction=False)


def apply_contradiction(
    kg: KnowledgeGraph,
    new_memory_id: str,
    result: ContradictionResult,
) -> None:
    """Apply contradiction relation to the knowledge graph."""
    if not result.has_contradiction or not result.conflicting_memory_id:
        return

    if kg.has_node(new_memory_id) and kg.has_node(result.conflicting_memory_id):
        kg.add_edge(
            new_memory_id,
            result.conflicting_memory_id,
            relation=result.relation_type,
            weight=result.similarity,
        )
