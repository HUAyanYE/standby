-- 用户 (5 个)
INSERT INTO users (phone_hash, internal_token, device_fingerprint, credit_score, marker_credit) VALUES ('hash_night', 'token_night', 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2', 0.5, 0.5) ON CONFLICT (phone_hash) DO NOTHING;
INSERT INTO users (phone_hash, internal_token, device_fingerprint, credit_score, marker_credit) VALUES ('hash_dawn', 'token_dawn', 'b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3', 0.5, 0.5) ON CONFLICT (phone_hash) DO NOTHING;
INSERT INTO users (phone_hash, internal_token, device_fingerprint, credit_score, marker_credit) VALUES ('hash_wind', 'token_wind', 'c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4', 0.5, 0.5) ON CONFLICT (phone_hash) DO NOTHING;
INSERT INTO users (phone_hash, internal_token, device_fingerprint, credit_score, marker_credit) VALUES ('hash_autumn', 'token_autumn', 'd4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5', 0.5, 0.5) ON CONFLICT (phone_hash) DO NOTHING;
INSERT INTO users (phone_hash, internal_token, device_fingerprint, credit_score, marker_credit) VALUES ('hash_winter', 'token_winter', 'e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6', 0.5, 0.5) ON CONFLICT (phone_hash) DO NOTHING;

-- 锚点 (15 条)
INSERT INTO anchors (id, creator_id, modality, text_content, topics, source, quality_score) VALUES ('a001', (SELECT id FROM users WHERE phone_hash='hash_night'), 'text', '小时候最喜欢下雨天，因为可以踩水坑。现在下雨天只想着别弄湿鞋。前天又下雨了，我撑着伞走在路上，看到一个小孩在踩水坑，突然很想脱了鞋也去踩。', '["童年","成长","下雨"]', 'user', 0.4) ON CONFLICT (id) DO NOTHING;
INSERT INTO anchors (id, creator_id, modality, text_content, topics, source, quality_score) VALUES ('a002', (SELECT id FROM users WHERE phone_hash='hash_dawn'), 'text', '整理旧物时翻到小学作文本，写的是我的梦想是当科学家。现在在写代码，也算某种意义上的科学家吧。只是这个科学家，经常加班到凌晨。', '["童年","梦想","成长"]', 'user', 0.4) ON CONFLICT (id) DO NOTHING;
INSERT INTO anchors (id, creator_id, modality, text_content, topics, source, quality_score) VALUES ('a003', (SELECT id FROM users WHERE phone_hash='hash_wind'), 'text', '小时候觉得大人什么都知道，长大后发现大人只是装作什么都知道。现在我也在装了，面对后辈的问题，总是说嗯这个嘛。', '["成长","人生","感悟"]', 'user', 0.4) ON CONFLICT (id) DO NOTHING;
INSERT INTO anchors (id, creator_id, modality, text_content, topics, source, quality_score) VALUES ('a004', (SELECT id FROM users WHERE phone_hash='hash_autumn'), 'text', '妈妈打电话来，问我吃了没。我说吃了。其实那天忘了吃午饭，一直在改一个bug。不想让她担心，所以每次都说吃了。', '["亲情","母亲","独居"]', 'user', 0.4) ON CONFLICT (id) DO NOTHING;
INSERT INTO anchors (id, creator_id, modality, text_content, topics, source, quality_score) VALUES ('a005', (SELECT id FROM users WHERE phone_hash='hash_winter'), 'text', '爸爸从不说想我，但每次我回家，桌上总有我爱吃的菜。走的时候，他会说路上慢点，然后转身进屋。我知道他在忍着不送我。', '["亲情","父爱","回家"]', 'user', 0.4) ON CONFLICT (id) DO NOTHING;

-- 反应 (使用 gen_random_uuid() 生成 ID)
INSERT INTO reactions (user_id, anchor_id, reaction_type, emotion_word, modality, text_content, resonance_value) VALUES ((SELECT id FROM users WHERE phone_hash='hash_dawn'), 'a001', 'resonance', 'empathy', 'text', '我也经历过类似的事情', 0.8);
INSERT INTO reactions (user_id, anchor_id, reaction_type, emotion_word, modality, text_content, resonance_value) VALUES ((SELECT id FROM users WHERE phone_hash='hash_wind'), 'a001', 'resonance', 'trigger', 'text', '这让我想起了小时候', 0.7);
INSERT INTO reactions (user_id, anchor_id, reaction_type, emotion_word, modality, text_content, resonance_value) VALUES ((SELECT id FROM users WHERE phone_hash='hash_autumn'), 'a002', 'neutral', NULL, 'text', '有点意思', 0.3);
INSERT INTO reactions (user_id, anchor_id, reaction_type, emotion_word, modality, text_content, resonance_value) VALUES ((SELECT id FROM users WHERE phone_hash='hash_winter'), 'a003', 'resonance', 'insight', 'text', '说出了我想说的话', 0.9);
INSERT INTO reactions (user_id, anchor_id, reaction_type, emotion_word, modality, text_content, resonance_value) VALUES ((SELECT id FROM users WHERE phone_hash='hash_night'), 'a004', 'resonance', 'empathy', 'text', '妈妈都是这样的', 0.85);
