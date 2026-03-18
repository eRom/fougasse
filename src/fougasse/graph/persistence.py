"""Bidirectional sync between NetworkX graph and SQLite."""

from __future__ import annotations

import sqlite3

from fougasse.graph.knowledge_graph import KnowledgeGraph
from fougasse.models import utcnow


def save_graph(kg: KnowledgeGraph, db: sqlite3.Connection) -> None:
    """Persist the full graph to SQLite (overwrite)."""
    with db:
        db.execute("DELETE FROM graph_edges")
        db.execute("DELETE FROM graph_nodes")

        now = utcnow().isoformat()

        for node_id, attrs in kg.graph.nodes(data=True):
            db.execute(
                """INSERT OR REPLACE INTO graph_nodes
                   (id, node_type, label, pagerank, community_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    node_id,
                    attrs.get("node_type", "memory"),
                    attrs.get("label", ""),
                    attrs.get("pagerank", 0.0),
                    attrs.get("community_id"),
                    now,
                ),
            )

        for source, target, attrs in kg.graph.edges(data=True):
            db.execute(
                """INSERT OR REPLACE INTO graph_edges
                   (source_id, target_id, relation, weight, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    source,
                    target,
                    attrs.get("relation", "relates_to"),
                    attrs.get("weight", 1.0),
                    now,
                ),
            )


def load_graph(db: sqlite3.Connection) -> KnowledgeGraph:
    """Load the graph from SQLite into a KnowledgeGraph."""
    kg = KnowledgeGraph()

    nodes = db.execute("SELECT * FROM graph_nodes").fetchall()
    for row in nodes:
        kg.graph.add_node(
            row["id"],
            node_type=row["node_type"],
            label=row["label"],
            pagerank=row["pagerank"],
            community_id=row["community_id"],
        )

    edges = db.execute("SELECT * FROM graph_edges").fetchall()
    for row in edges:
        kg.graph.add_edge(
            row["source_id"],
            row["target_id"],
            relation=row["relation"],
            weight=row["weight"],
        )

    return kg


def save_node(kg: KnowledgeGraph, db: sqlite3.Connection, node_id: str) -> None:
    """Save a single node and its edges incrementally."""
    if not kg.has_node(node_id):
        return

    attrs = kg.graph.nodes[node_id]
    now = utcnow().isoformat()

    with db:
        db.execute(
            """INSERT OR REPLACE INTO graph_nodes
               (id, node_type, label, pagerank, community_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                node_id,
                attrs.get("node_type", "memory"),
                attrs.get("label", ""),
                attrs.get("pagerank", 0.0),
                attrs.get("community_id"),
                now,
            ),
        )

        # Ensure target nodes exist before saving edges
        for _, target, eattrs in kg.graph.out_edges(node_id, data=True):
            if target in kg.graph:
                tattrs = kg.graph.nodes[target]
                db.execute(
                    """INSERT OR REPLACE INTO graph_nodes
                       (id, node_type, label, pagerank, community_id, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        target,
                        tattrs.get("node_type", "entity"),
                        tattrs.get("label", ""),
                        tattrs.get("pagerank", 0.0),
                        tattrs.get("community_id"),
                        now,
                    ),
                )

        # Save outgoing edges
        db.execute("DELETE FROM graph_edges WHERE source_id = ?", (node_id,))
        for _, target, eattrs in kg.graph.out_edges(node_id, data=True):
            db.execute(
                """INSERT OR REPLACE INTO graph_edges
                   (source_id, target_id, relation, weight, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    node_id,
                    target,
                    eattrs.get("relation", "relates_to"),
                    eattrs.get("weight", 1.0),
                    now,
                ),
            )
