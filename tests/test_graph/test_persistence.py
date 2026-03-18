"""Tests for graph persistence."""

from __future__ import annotations

from fougasse.graph.knowledge_graph import KnowledgeGraph
from fougasse.graph.persistence import load_graph, save_graph, save_node
from fougasse.storage.database import init_database


def test_save_and_load() -> None:
    db = init_database()
    kg = KnowledgeGraph()
    kg.add_memory_node("mem-1", "Memory 1")
    kg.add_memory_node("mem-2", "Memory 2")
    kg.add_entity_node("tag:python", "python")
    kg.add_edge("mem-1", "tag:python", relation="tagged_with")
    kg.add_edge("mem-1", "mem-2", relation="relates_to", weight=0.8)

    save_graph(kg, db)
    loaded = load_graph(db)

    assert loaded.node_count == 3
    assert loaded.edge_count == 2
    assert loaded.has_node("mem-1")
    assert loaded.has_edge("mem-1", "tag:python")
    db.close()


def test_save_node_incremental() -> None:
    db = init_database()
    kg = KnowledgeGraph()
    kg.add_memory_node("mem-1", "Memory 1")
    kg.add_entity_node("tag:rust", "rust")
    kg.add_edge("mem-1", "tag:rust", relation="tagged_with")

    save_node(kg, db, "mem-1")

    # Verify in DB
    node = db.execute("SELECT * FROM graph_nodes WHERE id = 'mem-1'").fetchone()
    assert node is not None
    assert node["label"] == "Memory 1"

    edge = db.execute("SELECT * FROM graph_edges WHERE source_id = 'mem-1'").fetchone()
    assert edge is not None
    assert edge["relation"] == "tagged_with"
    db.close()


def test_roundtrip_preserves_attributes() -> None:
    db = init_database()
    kg = KnowledgeGraph()
    kg.add_memory_node("mem-1", "Test", pagerank=0.42)
    kg.graph.nodes["mem-1"]["community_id"] = 3

    save_graph(kg, db)
    loaded = load_graph(db)

    attrs = loaded.get_node_attrs("mem-1")
    assert attrs["pagerank"] == 0.42
    assert attrs["community_id"] == 3
    db.close()
