-- Migration 004: Vector tables (pgvector)
-- 768 维语义向量, 使用 HNSW 索引加速余弦相似度搜索

-- 锚点向量表
CREATE TABLE IF NOT EXISTS anchor_vectors (
    anchor_id   TEXT PRIMARY KEY REFERENCES anchors(id) ON DELETE CASCADE,
    vector      vector(768) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anchor_vectors_hnsw
    ON anchor_vectors USING hnsw (vector vector_cosine_ops)
    WITH (ef_construction = 64, M = 16);

-- 共鸣向量表
CREATE TABLE IF NOT EXISTS resonance_vectors (
    id                  BIGSERIAL PRIMARY KEY,
    anchor_id           TEXT NOT NULL REFERENCES anchors(id) ON DELETE CASCADE,
    internal_token_hash TEXT NOT NULL,
    vector              vector(768) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resonance_vectors_anchor ON resonance_vectors(anchor_id);

CREATE INDEX IF NOT EXISTS idx_resonance_vectors_hnsw
    ON resonance_vectors USING hnsw (vector vector_cosine_ops)
    WITH (ef_construction = 64, M = 16);
