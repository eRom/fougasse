"""Graph-based retrieval via spreading activation."""

from __future__ import annotations

from fougasse.graph.knowledge_graph import KnowledgeGraph


def spreading_activation(
    kg: KnowledgeGraph,
    seed_ids: list[str],
    max_hops: int = 3,
    decay: float = 0.5,
    max_results: int = 30,
) -> list[tuple[str, float]]:
    """Spread activation from seed nodes through the graph.

    Returns (memory_id, activation_score) pairs for memory-type nodes only.
    """
    activation: dict[str, float] = {}

    # Initialize seeds
    for seed_id in seed_ids:
        if kg.has_node(seed_id):
            activation[seed_id] = 1.0

    # Spread through hops
    for hop in range(max_hops):
        factor = decay ** (hop + 1)
        new_activation: dict[str, float] = {}

        for node_id, score in activation.items():
            if not kg.has_node(node_id):
                continue

            # Spread to successors
            for neighbor in kg.graph.successors(node_id):
                edge_data = kg.graph.edges[node_id, neighbor]
                weight = edge_data.get("weight", 1.0)
                spread = score * factor * weight
                new_activation[neighbor] = max(new_activation.get(neighbor, 0.0), spread)

            # Spread to predecessors
            for neighbor in kg.graph.predecessors(node_id):
                edge_data = kg.graph.edges[neighbor, node_id]
                weight = edge_data.get("weight", 1.0)
                spread = score * factor * weight
                new_activation[neighbor] = max(new_activation.get(neighbor, 0.0), spread)

        # Merge new activations
        for node_id, score in new_activation.items():
            activation[node_id] = max(activation.get(node_id, 0.0), score)

    # Filter: only memory nodes, exclude seeds
    results = []
    seed_set = set(seed_ids)
    for node_id, score in activation.items():
        if node_id in seed_set:
            continue
        attrs = kg.get_node_attrs(node_id)
        if attrs and attrs.get("node_type") == "memory":
            results.append((node_id, score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:max_results]
