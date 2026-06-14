-- Migration 005: Reactions table
-- 五态反应: 共鸣 / 无感 / 反对 / 未体验 / 有害
-- 支持感受链: parent_reaction_id 形成树状结构

CREATE TABLE IF NOT EXISTS reactions (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             TEXT NOT NULL,
    anchor_id           TEXT NOT NULL REFERENCES anchors(id) ON DELETE CASCADE,
    reaction_type       TEXT NOT NULL
        CHECK (reaction_type IN ('共鸣', '无感', '反对', '未体验', '有害')),
    emotion_word        TEXT
        CHECK (emotion_word IS NULL OR emotion_word IN ('同感', '触发', '启发', '震撼')),
    modality            TEXT NOT NULL DEFAULT 'text',
    text_content        TEXT,
    resonance_value     REAL DEFAULT 0.0,
    parent_reaction_id  BIGINT REFERENCES reactions(id),
    root_reaction_id    BIGINT REFERENCES reactions(id),
    depth               SMALLINT NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reactions_anchor_id ON reactions(anchor_id);
CREATE INDEX IF NOT EXISTS idx_reactions_user_id ON reactions(user_id);
CREATE INDEX IF NOT EXISTS idx_reactions_type ON reactions(reaction_type);
CREATE INDEX IF NOT EXISTS idx_reactions_parent ON reactions(parent_reaction_id) WHERE parent_reaction_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reactions_root ON reactions(root_reaction_id) WHERE root_reaction_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reactions_created_at ON reactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reactions_anchor_type ON reactions(anchor_id, reaction_type);
