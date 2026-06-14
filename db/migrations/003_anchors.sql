-- Migration 003: Anchors table
-- 锚点 = 用户表达的载体, 心物 = 被识别为有情感价值的锚点

CREATE TABLE IF NOT EXISTS anchors (
    id              TEXT PRIMARY KEY,
    text_content    TEXT NOT NULL,
    topics          JSONB NOT NULL DEFAULT '[]',
    source          TEXT NOT NULL DEFAULT 'user',
    modality        TEXT NOT NULL DEFAULT 'text',
    quality_score   REAL NOT NULL DEFAULT 0.0,
    is_seedstone    BOOLEAN NOT NULL DEFAULT FALSE,
    seedstone_confidence REAL DEFAULT 0.0,
    parent_anchor_id TEXT REFERENCES anchors(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anchors_source ON anchors(source);
CREATE INDEX IF NOT EXISTS idx_anchors_is_seedstone ON anchors(is_seedstone) WHERE is_seedstone = TRUE;
CREATE INDEX IF NOT EXISTS idx_anchors_created_at ON anchors(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_anchors_topics ON anchors USING GIN(topics);
