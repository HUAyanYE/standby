-- Migration 009: Seed data (development only)
-- 仅在 DEVELOPMENT_SEED=true 环境变量设置时执行

-- 插入测试用户
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
