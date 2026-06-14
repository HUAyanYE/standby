-- Migration 006: Relationships table
-- 关系深度是光谱 0-100, 不是二元的
-- user_a_hash < user_b_hash 保证唯一性

CREATE TABLE IF NOT EXISTS relationships (
    user_a_hash         TEXT NOT NULL,
    user_b_hash         TEXT NOT NULL,
    score_a_to_b        REAL NOT NULL DEFAULT 0.0,
    score_b_to_a        REAL NOT NULL DEFAULT 0.0,
    topic_diversity     INTEGER NOT NULL DEFAULT 0,
    shared_anchors      INTEGER NOT NULL DEFAULT 0,
    last_resonance_at   TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_a_hash, user_b_hash),
    CHECK (user_a_hash < user_b_hash)
);

CREATE INDEX IF NOT EXISTS idx_relationships_user_a ON relationships(user_a_hash);
CREATE INDEX IF NOT EXISTS idx_relationships_user_b ON relationships(user_b_hash);
CREATE INDEX IF NOT EXISTS idx_relationships_score ON relationships(score_a_to_b DESC);
CREATE INDEX IF NOT EXISTS idx_relationships_last_resonance ON relationships(last_resonance_at DESC);
