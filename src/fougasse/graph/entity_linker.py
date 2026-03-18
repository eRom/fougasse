"""Automatic edge creation based on tags, entities, and semantic proximity."""

from __future__ import annotations

from fougasse.graph.knowledge_graph import KnowledgeGraph
from fougasse.models import Memory


def link_memory(kg: KnowledgeGraph, memory: Memory) -> int:
    """Create graph edges for a newly inserted memory. Returns number of edges created."""
    edges_created = 0

    # Add memory node
    kg.add_memory_node(memory.id, label=memory.content[:80])

    # Create entity nodes for tags and link them
    for tag in memory.tags:
        entity_id = f"tag:{tag}"
        if not kg.has_node(entity_id):
            kg.add_entity_node(entity_id, label=tag)
        kg.add_edge(memory.id, entity_id, relation="tagged_with")
        edges_created += 1

    # Find other memories sharing 2+ tags and create relates_to edges
    if len(memory.tags) >= 2:
        _link_by_shared_tags(kg, memory)

    return edges_created


def _link_by_shared_tags(kg: KnowledgeGraph, memory: Memory) -> None:
    """Create relates_to edges between memories sharing 2+ tags."""
    tag_entities = {f"tag:{t}" for t in memory.tags}

    for node_id in list(kg.graph.nodes):
        if node_id == memory.id:
            continue
        attrs = kg.get_node_attrs(node_id)
        if attrs is None or attrs.get("node_type") != "memory":
            continue

        # Count shared tag entities
        node_tags = set()
        for _, target, data in kg.graph.out_edges(node_id, data=True):
            if data.get("relation") == "tagged_with":
                node_tags.add(target)

        shared = tag_entities & node_tags
        if len(shared) >= 2:
            weight = len(shared) / max(len(tag_entities), len(node_tags))
            if not kg.has_edge(memory.id, node_id):
                kg.add_edge(memory.id, node_id, relation="relates_to", weight=weight)
            if not kg.has_edge(node_id, memory.id):
                kg.add_edge(node_id, memory.id, relation="relates_to", weight=weight)


def link_by_similarity(
    kg: KnowledgeGraph,
    memory_id: str,
    similar_ids: list[tuple[str, float]],
    threshold: float = 0.8,
) -> int:
    """Create relates_to edges based on semantic similarity. Returns edges created."""
    edges_created = 0
    for other_id, distance in similar_ids:
        if other_id == memory_id:
            continue
        # Convert distance to similarity (assuming L2 distance on normalized vectors)
        similarity = max(0.0, 1.0 - distance / 2.0)
        if similarity >= threshold and kg.has_node(other_id):
            if not kg.has_edge(memory_id, other_id):
                kg.add_edge(memory_id, other_id, relation="relates_to", weight=similarity)
                edges_created += 1
    return edges_created
