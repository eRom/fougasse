"""PageRank computation and community detection."""

from __future__ import annotations

import networkx as nx

from fougasse.graph.knowledge_graph import KnowledgeGraph


def compute_pagerank(kg: KnowledgeGraph, alpha: float = 0.85) -> dict[str, float]:
    """Compute PageRank scores and store them in node attributes.

    Returns dict of {node_id: pagerank_score}.
    """
    if kg.node_count == 0:
        return {}

    scores = nx.pagerank(kg.graph, alpha=alpha)

    # Store in node attributes
    for node_id, score in scores.items():
        kg.graph.nodes[node_id]["pagerank"] = score

    return dict(scores)


def detect_communities(kg: KnowledgeGraph) -> dict[str, int]:
    """Detect communities using greedy modularity (no leidenalg dependency required).

    Falls back to connected components if modularity fails.
    Returns dict of {node_id: community_id}.
    """
    if kg.node_count == 0:
        return {}

    # Convert to undirected for community detection
    undirected = kg.graph.to_undirected()

    try:
        # Try greedy modularity communities
        communities = nx.community.greedy_modularity_communities(undirected)
        mapping: dict[str, int] = {}
        for idx, community in enumerate(communities):
            for node_id in community:
                mapping[node_id] = idx
                kg.graph.nodes[node_id]["community_id"] = idx
        return mapping
    except Exception:
        # Fallback to connected components
        mapping = {}
        for idx, component in enumerate(nx.connected_components(undirected)):
            for node_id in component:
                mapping[node_id] = idx
                kg.graph.nodes[node_id]["community_id"] = idx
        return mapping


def get_community_summary(kg: KnowledgeGraph) -> list[dict[str, object]]:
    """Get summary of detected communities."""
    communities: dict[int, list[str]] = {}

    for node_id, attrs in kg.graph.nodes(data=True):
        cid = attrs.get("community_id")
        if cid is not None:
            communities.setdefault(cid, []).append(node_id)

    return [
        {
            "community_id": cid,
            "node_count": len(nodes),
            "nodes": nodes[:10],  # First 10 for preview
        }
        for cid, nodes in sorted(communities.items())
    ]
