-- Migration 007: Governance decisions table
-- 内容治理的决策日志

CREATE TABLE IF NOT EXISTS governance_decisions (
    id                  BIGSERIAL PRIMARY KEY,
    content_id          TEXT NOT NULL,
    content_type        TEXT NOT NULL DEFAULT 'anchor',
    level               TEXT NOT NULL DEFAULT 'L0_NORMAL',
    harmful_weight      REAL NOT NULL DEFAULT 0.0,
    marker_avg_credit   REAL NOT NULL DEFAULT 0.5,
    reason              TEXT NOT NULL DEFAULT '',
    actions             JSONB NOT NULL DEFAULT '[]',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_governance_content_id ON governance_decisions(content_id);
CREATE INDEX IF NOT EXISTS idx_governance_level ON governance_decisions(level);
CREATE INDEX IF NOT EXISTS idx_governance_created_at ON governance_decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_governance_content_created ON governance_decisions(content_id, created_at DESC);
