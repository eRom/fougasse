-- Fougasse schema v002 — Vitality tracking enhancements
-- Add pinned flag and vitality index

CREATE INDEX IF NOT EXISTS idx_memories_vitality_active
    ON memories(vitality_score) WHERE is_archived = 0;

INSERT INTO schema_version (version) VALUES (2);
