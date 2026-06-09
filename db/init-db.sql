-- ============================================================
-- Standby 数据库初始化脚本
-- ============================================================
-- PostgreSQL 16 + pgvector 扩展
-- 运行方式: 自动通过 docker-entrypoint-initdb.d 执行
-- ============================================================

-- 启用扩展
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;      -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- 文本模糊搜索

-- ============================================================
-- 1. 用户表 (匿名身份)
-- ============================================================
-- 设计原则: 不存储任何 PII, 只有设备指纹哈希
CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_hash          TEXT UNIQUE,                    -- 手机号哈希 (可选, 用于找回)
    internal_token      TEXT UNIQUE NOT NULL,           -- 内部令牌哈希 (设备指纹派生)
    device_fingerprint  TEXT NOT NULL,                  -- 设备指纹
    marker_credit       REAL NOT NULL DEFAULT 0.5,      -- 标记者信用分 (Bayesian)
    trust_level         SMALLINT NOT NULL DEFAULT 1,    -- 信任等级 1-4
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_internal_token ON users(internal_token);
CREATE INDEX IF NOT EXISTS idx_users_device_fingerprint ON users(device_fingerprint);

-- ============================================================
-- 2. 锚点表 (心物元数据)
-- ============================================================
-- 锚点 = 用户表达的载体, 心物 = 被识别为有情感价值的锚点
CREATE TABLE IF NOT EXISTS anchors (
    id              TEXT PRIMARY KEY,                   -- 锚点 ID (a_xxxxxxxx)
    text_content    TEXT NOT NULL,                      -- 锚点文本
    topics          JSONB NOT NULL DEFAULT '[]',        -- 话题标签 ["孤独", "城市"]
    source          TEXT NOT NULL DEFAULT 'user',       -- 来源: user / platform_initial / aggregated
    modality        TEXT NOT NULL DEFAULT 'text',       -- 模态: text / image / video / audio
    quality_score   REAL NOT NULL DEFAULT 0.0,          -- 质量评分 0-1
    is_seedstone    BOOLEAN NOT NULL DEFAULT FALSE,     -- 是否被识别为心物
    seedstone_confidence REAL DEFAULT 0.0,              -- 心物置信度
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_anchors_source ON anchors(source);
CREATE INDEX IF NOT EXISTS idx_anchors_is_seedstone ON anchors(is_seedstone) WHERE is_seedstone = TRUE;
CREATE INDEX IF NOT EXISTS idx_anchors_created_at ON anchors(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_anchors_topics ON anchors USING GIN(topics);

-- ============================================================
-- 3. 锚点向量表 (pgvector)
-- ============================================================
-- 768 维语义向量, 使用 HNSW 索引加速余弦相似度搜索
CREATE TABLE IF NOT EXISTS anchor_vectors (
    anchor_id   TEXT PRIMARY KEY REFERENCES anchors(id) ON DELETE CASCADE,
    vector      vector(768) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- HNSW 索引: 余弦距离, ef_construction=64, M=16
CREATE INDEX IF NOT EXISTS idx_anchor_vectors_hnsw
    ON anchor_vectors USING hnsw (vector vector_cosine_ops)
    WITH (ef_construction = 64, M = 16);

-- ============================================================
-- 4. 反应表 (用户对锚点的反应)
-- ============================================================
-- 五态反应: 共鸣 / 无感 / 反对 / 未体验 / 有害
-- 支持感受链: parent_reaction_id 形成树状结构
CREATE TABLE IF NOT EXISTS reactions (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             TEXT NOT NULL,                      -- 用户内部令牌哈希
    anchor_id           TEXT NOT NULL REFERENCES anchors(id) ON DELETE CASCADE,
    reaction_type       TEXT NOT NULL,                      -- 共鸣/无感/反对/未体验/有害
    emotion_word        TEXT,                               -- 情绪词: 同感/触发/启发/震撼
    modality            TEXT NOT NULL DEFAULT 'text',       -- 模态
    text_content        TEXT,                               -- 观点文本
    resonance_value     REAL DEFAULT 0.0,                   -- 共鸣值
    parent_reaction_id  BIGINT REFERENCES reactions(id),    -- 父反应 (感受链)
    root_reaction_id    BIGINT REFERENCES reactions(id),    -- 根反应 (感受链)
    depth               SMALLINT NOT NULL DEFAULT 0,        -- 深度 (感受链层级)
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reactions_anchor_id ON reactions(anchor_id);
CREATE INDEX IF NOT EXISTS idx_reactions_user_id ON reactions(user_id);
CREATE INDEX IF NOT EXISTS idx_reactions_type ON reactions(reaction_type);
CREATE INDEX IF NOT EXISTS idx_reactions_parent ON reactions(parent_reaction_id) WHERE parent_reaction_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reactions_root ON reactions(root_reaction_id) WHERE root_reaction_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_reactions_created_at ON reactions(created_at DESC);

-- ============================================================
-- 5. 共鸣向量表 (pgvector)
-- ============================================================
-- 用户观点的语义向量, 用于 k-NN 相似度搜索
CREATE TABLE IF NOT EXISTS resonance_vectors (
    id                  BIGSERIAL PRIMARY KEY,
    anchor_id           TEXT NOT NULL REFERENCES anchors(id) ON DELETE CASCADE,
    internal_token_hash TEXT NOT NULL,                      -- 用户内部令牌哈希
    vector              vector(768) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resonance_vectors_anchor ON resonance_vectors(anchor_id);

-- HNSW 索引: 余弦距离
CREATE INDEX IF NOT EXISTS idx_resonance_vectors_hnsw
    ON resonance_vectors USING hnsw (vector vector_cosine_ops)
    WITH (ef_construction = 64, M = 16);

-- ============================================================
-- 6. 关系表 (用户间关系光谱)
-- ============================================================
-- 关系深度是光谱 0-100, 不是二元的
-- user_a_hash < user_b_hash 保证唯一性
CREATE TABLE IF NOT EXISTS relationships (
    user_a_hash         TEXT NOT NULL,
    user_b_hash         TEXT NOT NULL,
    score_a_to_b        REAL NOT NULL DEFAULT 0.0,          -- A 对 B 的关系分
    score_b_to_a        REAL NOT NULL DEFAULT 0.0,          -- B 对 A 的关系分
    topic_diversity     INTEGER NOT NULL DEFAULT 0,         -- 共同话题多样性
    shared_anchors      INTEGER NOT NULL DEFAULT 0,         -- 共同锚点数
    last_resonance_at   TIMESTAMPTZ,                        -- 最后共鸣时间
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_a_hash, user_b_hash),
    CHECK (user_a_hash < user_b_hash)                       -- 保证排序一致性
);

CREATE INDEX IF NOT EXISTS idx_relationships_user_a ON relationships(user_a_hash);
CREATE INDEX IF NOT EXISTS idx_relationships_user_b ON relationships(user_b_hash);
CREATE INDEX IF NOT EXISTS idx_relationships_score ON relationships(score_a_to_b DESC);

-- ============================================================
-- 7. 治理决策表
-- ============================================================
-- 内容治理的决策日志
CREATE TABLE IF NOT EXISTS governance_decisions (
    id                  BIGSERIAL PRIMARY KEY,
    content_id          TEXT NOT NULL,                       -- 内容 ID (通常是锚点 ID)
    content_type        TEXT NOT NULL DEFAULT 'anchor',      -- 内容类型
    level               TEXT NOT NULL DEFAULT 'L0_NORMAL',   -- 治理级别
    harmful_weight      REAL NOT NULL DEFAULT 0.0,           -- 有害权重
    marker_avg_credit   REAL NOT NULL DEFAULT 0.5,           -- 标记者平均信用
    reason              TEXT NOT NULL DEFAULT '',             -- 决策原因
    actions             JSONB NOT NULL DEFAULT '[]',         -- 执行的动作
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_governance_content_id ON governance_decisions(content_id);
CREATE INDEX IF NOT EXISTS idx_governance_level ON governance_decisions(level);
CREATE INDEX IF NOT EXISTS idx_governance_created_at ON governance_decisions(created_at DESC);

-- ============================================================
-- 8. 用户情境表
-- ============================================================
-- 端侧上报的用户当前情境状态
CREATE TABLE IF NOT EXISTS user_contexts (
    user_id             TEXT PRIMARY KEY,
    scene_type          TEXT NOT NULL DEFAULT '',             -- 场景类型: commute/home_relax/work_break/driving/深夜
    mood_hint           TEXT NOT NULL DEFAULT '',             -- 情绪暗示: calm/reflective/energetic/tired
    attention_level     TEXT NOT NULL DEFAULT '',             -- 注意力水平: focused/scattered/idle
    device              SMALLINT NOT NULL DEFAULT 0,         -- 活跃设备: 1=手机 2=平板 3=PC
    context_timestamp   BIGINT NOT NULL DEFAULT 0,           -- 端侧时间戳
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- 9. 种子数据 (开发环境)
-- ============================================================

-- 插入测试用户 (仅开发环境)
INSERT INTO users (id, phone_hash, internal_token, device_fingerprint, marker_credit, trust_level)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'hash_dev_001', 'token_dev_001', 'fp_dev_001', 0.8, 3),
    ('00000000-0000-0000-0000-000000000002', 'hash_dev_002', 'token_dev_002', 'fp_dev_002', 0.6, 2),
    ('00000000-0000-0000-0000-000000000003', 'hash_dev_003', 'token_dev_003', 'fp_dev_003', 0.5, 1)
ON CONFLICT (internal_token) DO NOTHING;

-- 插入测试锚点
INSERT INTO anchors (id, text_content, topics, source, quality_score, is_seedstone)
VALUES
    ('a_seed_001', '每天早上挤地铁的时候，我都会想起小时候在乡下坐拖拉机的日子。那时候觉得慢，现在觉得挤。', '["通勤", "回忆", "城市"]', 'platform_initial', 0.85, TRUE),
    ('a_seed_002', '深夜一个人在便利店吃关东煮，看着窗外的霓虹灯，突然觉得这座城市既陌生又温暖。', '["深夜", "城市", "孤独"]', 'platform_initial', 0.90, TRUE),
    ('a_seed_003', '毕业那天，我们把学士帽扔向天空，以为自由了，后来才知道，那才是最自由的时刻。', '["毕业", "成长", "青春"]', 'platform_initial', 0.92, TRUE)
ON CONFLICT (id) DO NOTHING;

-- 完成
DO $$
BEGIN
    RAISE NOTICE '✅ Standby 数据库初始化完成';
    RAISE NOTICE '   - 用户表 (users)';
    RAISE NOTICE '   - 锚点表 (anchors)';
    RAISE NOTICE '   - 锚点向量表 (anchor_vectors, pgvector)';
    RAISE NOTICE '   - 反应表 (reactions, 感受链)';
    RAISE NOTICE '   - 共鸣向量表 (resonance_vectors, pgvector)';
    RAISE NOTICE '   - 关系表 (relationships)';
    RAISE NOTICE '   - 治理决策表 (governance_decisions)';
    RAISE NOTICE '   - 用户情境表 (user_contexts)';
END $$;
