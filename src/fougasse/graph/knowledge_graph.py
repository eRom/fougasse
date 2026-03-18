"""NetworkX-based knowledge graph for Fougasse."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx


@dataclass
class KnowledgeGraph:
    """In-memory directed knowledge graph backed by NetworkX."""

    graph: nx.DiGraph = field(default_factory=nx.DiGraph)

    # Valid relation types
    RELATION_TYPES = frozenset({
        "relates_to",
        "supersedes",
        "conflicts_with",
        "tagged_with",
    })

    def add_memory_node(self, memory_id: str, label: str, **attrs: Any) -> None:
        """Add a memory node to the graph."""
        self.graph.add_node(memory_id, node_type="memory", label=label, **attrs)

    def add_entity_node(self, entity_id: str, label: str, **attrs: Any) -> None:
        """Add an entity node (tag, concept) to the graph."""
        self.graph.add_node(entity_id, node_type="entity", label=label, **attrs)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        weight: float = 1.0,
    ) -> None:
        """Add a directed edge between two nodes."""
        if relation not in self.RELATION_TYPES:
            msg = f"Invalid relation '{relation}'. Valid: {self.RELATION_TYPES}"
            raise ValueError(msg)
        self.graph.add_edge(source_id, target_id, relation=relation, weight=weight)

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges. Returns True if removed."""
        if node_id not in self.graph:
            return False
        self.graph.remove_node(node_id)
        return True

    def remove_edge(self, source_id: str, target_id: str) -> bool:
        """Remove an edge. Returns True if removed."""
        if not self.graph.has_edge(source_id, target_id):
            return False
        self.graph.remove_edge(source_id, target_id)
        return True

    def get_neighbors(self, node_id: str, depth: int = 1) -> list[dict[str, Any]]:
        """Get neighboring nodes up to a given depth."""
        if node_id not in self.graph:
            return []

        visited: set[str] = set()
        result: list[dict[str, Any]] = []
        queue: list[tuple[str, int]] = [(node_id, 0)]

        while queue:
            current, d = queue.pop(0)
            if current in visited or d > depth:
                continue
            visited.add(current)

            if current != node_id:
                attrs = dict(self.graph.nodes[current])
                result.append({"id": current, "depth": d, **attrs})

            if d < depth:
                for neighbor in self.graph.successors(current):
                    if neighbor not in visited:
                        queue.append((neighbor, d + 1))
                for neighbor in self.graph.predecessors(current):
                    if neighbor not in visited:
                        queue.append((neighbor, d + 1))

        return result

    def get_subgraph(self, node_id: str, depth: int = 2) -> dict[str, Any]:
        """Get a subgraph around a node for exploration."""
        if node_id not in self.graph:
            return {"nodes": [], "edges": []}

        neighbors = self.get_neighbors(node_id, depth=depth)
        node_ids = {node_id} | {n["id"] for n in neighbors}

        nodes = []
        for nid in node_ids:
            if nid in self.graph:
                attrs = dict(self.graph.nodes[nid])
                nodes.append({"id": nid, **attrs})

        edges = []
        for u, v, data in self.graph.edges(data=True):
            if u in node_ids and v in node_ids:
                edges.append({"source": u, "target": v, **data})

        return {"nodes": nodes, "edges": edges}

    def get_edges_for_node(self, node_id: str) -> list[dict[str, Any]]:
        """Get all edges connected to a node."""
        if node_id not in self.graph:
            return []

        edges = []
        for u, v, data in self.graph.out_edges(node_id, data=True):
            edges.append({"source": u, "target": v, **data})
        for u, v, data in self.graph.in_edges(node_id, data=True):
            edges.append({"source": u, "target": v, **data})
        return edges

    @property
    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def has_node(self, node_id: str) -> bool:
        return node_id in self.graph

    def has_edge(self, source_id: str, target_id: str) -> bool:
        return self.graph.has_edge(source_id, target_id)

    def get_node_attrs(self, node_id: str) -> dict[str, Any] | None:
        if node_id not in self.graph:
            return None
        return dict(self.graph.nodes[node_id])
