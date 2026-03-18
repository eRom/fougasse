-- Fougasse schema v001 — Core tables
-- Memories, vaults, tags, access log, knowledge graph, vec0, FTS5

-- Vaults (namespaces)
CREATE TABLE IF NOT EXISTS vaults (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Default vault
INSERT OR IGNORE INTO vaults (id, name, description, created_at)
VALUES ('default', 'default', 'Default vault', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));

-- Memories
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'text',
    vault_id TEXT NOT NULL DEFAULT 'default',
    source_agent TEXT,
    metadata TEXT,  -- JSON
    vitality_score REAL NOT NULL DEFAULT 1.0,
    access_count INTEGER NOT NULL DEFAULT 0,
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (vault_id) REFERENCES vaults(id)
);

CREATE INDEX IF NOT EXISTS idx_memories_vault ON memories(vault_id);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_archived ON memories(is_archived);
CREATE INDEX IF NOT EXISTS idx_memories_vitality ON memories(vitality_score);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);

-- Tags (many-to-many)
CREATE TABLE IF NOT EXISTS tags (
    memory_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    PRIMARY KEY (memory_id, tag),
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);

-- Access log (for ACT-R vitality)
CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id TEXT NOT NULL,
    accessed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_access_log_memory ON access_log(memory_id);

-- Knowledge graph: nodes
CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL DEFAULT 'memory',  -- 'memory' or 'entity'
    label TEXT NOT NULL,
    pagerank REAL NOT NULL DEFAULT 0.0,
    community_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(node_type);

-- Knowledge graph: edges
CREATE TABLE IF NOT EXISTS graph_edges (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation TEXT NOT NULL,  -- relates_to, supersedes, conflicts_with, tagged_with
    weight REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (source_id, target_id, relation),
    FOREIGN KEY (source_id) REFERENCES graph_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES graph_nodes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_target ON graph_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_relation ON graph_edges(relation);

-- FTS5 full-text search index (standalone, no content sync — managed in Python)
CREATE VIRTUAL TABLE IF NOT EXISTS fts_memories USING fts5(
    memory_id UNINDEXED,
    content,
    tags
);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

INSERT INTO schema_version (version) VALUES (1);
