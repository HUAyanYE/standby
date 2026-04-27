-- ============================================================
-- Standby PostgreSQL 初始化脚本
-- ============================================================
-- 架构: PostgreSQL一体化 (无MongoDB)
-- 所有数据存储在 PostgreSQL
-- ============================================================

-- 启用扩展
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- 用户
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    real_name BYTEA,
    phone_hash TEXT UNIQUE NOT NULL,
    internal_token TEXT UNIQUE NOT NULL,
    device_fingerprint TEXT NOT NULL,
    credit_score FLOAT DEFAULT 0.5,
    marker_credit FLOAT DEFAULT 0.5,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 认证凭证
-- ============================================================
CREATE TABLE IF NOT EXISTS auth_credentials (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    credential_type TEXT NOT NULL,
    credential_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 媒体文件 (元数据, 实际文件在 MinIO)
-- ============================================================
CREATE TABLE IF NOT EXISTS media (
    id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    media_type TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    storage_url TEXT NOT NULL,
    thumbnail_url TEXT,
    file_size_bytes BIGINT NOT NULL,
    duration_seconds FLOAT,
    width INT,
    height INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_media_owner ON media (owner_id, created_at DESC);

-- ============================================================
-- 锚点 (多模态)
-- ============================================================
CREATE TABLE IF NOT EXISTS anchors (
    id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL,
    modality TEXT NOT NULL DEFAULT 'text',
    text_content TEXT,
    topics JSONB DEFAULT '[]',
    source TEXT DEFAULT 'user',
    quality_score FLOAT DEFAULT 0,
    vector vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anchors_creator ON anchors (creator_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_anchors_topics ON anchors USING GIN (topics);
CREATE INDEX IF NOT EXISTS idx_anchors_source ON anchors (source, created_at DESC);

-- ============================================================
-- 锚点-媒体关联
-- ============================================================
CREATE TABLE IF NOT EXISTS anchor_media (
    anchor_id UUID REFERENCES anchors(id) ON DELETE CASCADE,
    media_id UUID REFERENCES media(id) ON DELETE CASCADE,
    display_order INT DEFAULT 0,
    PRIMARY KEY (anchor_id, media_id)
);

-- ============================================================
-- 用户表达 (多模态)
-- ============================================================
CREATE TABLE IF NOT EXISTS reactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    anchor_id UUID REFERENCES anchors(id) ON DELETE CASCADE,
    reaction_type TEXT NOT NULL,
    emotion_word TEXT,
    modality TEXT NOT NULL DEFAULT 'text',
    text_content TEXT,
    resonance_value FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reactions_user ON reactions (user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reactions_anchor ON reactions (anchor_id, created_at DESC);

-- ============================================================
-- 表达-媒体关联
-- ============================================================
CREATE TABLE IF NOT EXISTS reaction_media (
    reaction_id UUID REFERENCES reactions(id) ON DELETE CASCADE,
    media_id UUID REFERENCES media(id) ON DELETE CASCADE,
    display_order INT DEFAULT 0,
    PRIMARY KEY (reaction_id, media_id)
);

-- ============================================================
-- 向量存储 (pgvector 备份)
-- ============================================================
CREATE TABLE IF NOT EXISTS resonance_vectors (
    id TEXT PRIMARY KEY,
    anchor_id TEXT NOT NULL,
    internal_token_hash TEXT NOT NULL,
    vector vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resonance_vectors_vector
    ON resonance_vectors USING hnsw (vector vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_resonance_vectors_anchor
    ON resonance_vectors (anchor_id);

CREATE TABLE IF NOT EXISTS anchor_vectors (
    id TEXT PRIMARY KEY,
    anchor_id TEXT UNIQUE NOT NULL,
    vector vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anchor_vectors_vector
    ON anchor_vectors USING hnsw (vector vector_cosine_ops);

-- ============================================================
-- 匿名身份
-- ============================================================
CREATE TABLE IF NOT EXISTS anonymous_identities (
    id TEXT PRIMARY KEY,
    internal_token_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    avatar_seed TEXT NOT NULL,
    anchor_id UUID REFERENCES anchors(id),
    is_fixed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(internal_token_hash, anchor_id)
);

CREATE INDEX IF NOT EXISTS idx_anon_identities_anchor ON anonymous_identities (anchor_id);

-- ============================================================
-- 关系
-- ============================================================
CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    user_a_hash TEXT NOT NULL,
    user_b_hash TEXT NOT NULL,
    score_a_to_b FLOAT DEFAULT 0,
    score_b_to_a FLOAT DEFAULT 0,
    topic_diversity INT DEFAULT 0,
    trust_level INT DEFAULT 0,
    a_intent_expressed BOOLEAN DEFAULT false,
    b_intent_expressed BOOLEAN DEFAULT false,
    is_confidant BOOLEAN DEFAULT false,
    first_resonance_at TIMESTAMPTZ,
    last_resonance_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_a_hash, user_b_hash)
);

CREATE INDEX IF NOT EXISTS idx_relationships_a ON relationships (user_a_hash);
CREATE INDEX IF NOT EXISTS idx_relationships_b ON relationships (user_b_hash);

-- ============================================================
-- 治理决策
-- ============================================================
CREATE TABLE IF NOT EXISTS governance_decisions (
    id TEXT PRIMARY KEY,
    content_id TEXT NOT NULL,
    content_type TEXT NOT NULL,
    level TEXT NOT NULL,
    harmful_weight FLOAT,
    marker_avg_credit FLOAT,
    reason TEXT,
    actions TEXT[],
    decided_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_governance_decisions_content ON governance_decisions (content_id);
CREATE INDEX IF NOT EXISTS idx_governance_decisions_time ON governance_decisions (decided_at DESC);

-- ============================================================
-- 申诉记录
-- ============================================================
CREATE TABLE IF NOT EXISTS appeal_records (
    id TEXT PRIMARY KEY,
    decision_id UUID REFERENCES governance_decisions(id),
    user_id UUID REFERENCES users(id),
    appeal_reason TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- ============================================================
-- 用户上下文授权
-- ============================================================
CREATE TABLE IF NOT EXISTS user_context_preferences (
    user_id TEXT PRIMARY KEY,
    location_enabled BOOLEAN DEFAULT false,
    weather_enabled BOOLEAN DEFAULT true,
    calendar_enabled BOOLEAN DEFAULT false,
    app_usage_enabled BOOLEAN DEFAULT false,
    notification_enabled BOOLEAN DEFAULT false,
    notification_time TIME DEFAULT '09:00',
    max_candidates_per_day INT DEFAULT 3,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 上下文事件
-- ============================================================
CREATE TABLE IF NOT EXISTS context_events (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    context_type TEXT NOT NULL,
    raw_data JSONB NOT NULL,
    processed_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_context_events_user ON context_events (user_id, created_at DESC);

-- ============================================================
-- 锚点候选
-- ============================================================
CREATE TABLE IF NOT EXISTS anchor_candidates (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    source_context_id UUID REFERENCES context_events(id),
    anchor_text TEXT NOT NULL,
    topics JSONB DEFAULT '[]',
    relevance_score FLOAT DEFAULT 0,
    status TEXT DEFAULT 'pending',
    presented_at TIMESTAMPTZ,
    responded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anchor_candidates_user ON anchor_candidates (user_id, status, created_at DESC);

-- ============================================================
-- 行级安全策略 (RLS)
-- ============================================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth_credentials ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_self_access ON users
    FOR ALL
    USING (id = current_setting('app.current_user_id', true)::UUID);

CREATE POLICY auth_self_access ON auth_credentials
    FOR ALL
    USING (user_id = current_setting('app.current_user_id', true)::UUID);
