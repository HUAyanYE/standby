-- 关系数据 (5 个用户两两之间)
INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level) VALUES ('hash_night', 'hash_dawn', 0.65, 0.70, 2) ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING;
INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level) VALUES ('hash_night', 'hash_wind', 0.45, 0.50, 1) ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING;
INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level) VALUES ('hash_night', 'hash_autumn', 0.30, 0.35, 0) ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING;
INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level) VALUES ('hash_night', 'hash_winter', 0.55, 0.60, 1) ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING;
INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level) VALUES ('hash_dawn', 'hash_wind', 0.72, 0.68, 3) ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING;
INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level) VALUES ('hash_dawn', 'hash_autumn', 0.40, 0.42, 1) ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING;
INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level) VALUES ('hash_dawn', 'hash_winter', 0.58, 0.55, 2) ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING;
INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level) VALUES ('hash_wind', 'hash_autumn', 0.35, 0.38, 0) ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING;
INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level) VALUES ('hash_wind', 'hash_winter', 0.48, 0.50, 1) ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING;
INSERT INTO relationships (user_a_hash, user_b_hash, score_a_to_b, score_b_to_a, trust_level) VALUES ('hash_autumn', 'hash_winter', 0.62, 0.65, 2) ON CONFLICT (user_a_hash, user_b_hash) DO NOTHING;
