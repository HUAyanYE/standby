-- 批量生成反应 (目标: ~500 条)
-- 每个锚点 30-35 条反应，15 个锚点 = ~500 条

DO $$
DECLARE
    anchor_rec RECORD;
    user_hash TEXT;
    rt TEXT;
    ew TEXT;
    txt TEXT;
    rv FLOAT;
    i INT;
    hashes TEXT[] := ARRAY['hash_night', 'hash_dawn', 'hash_wind', 'hash_autumn', 'hash_winter'];
    types TEXT[] := ARRAY['resonance', 'resonance', 'resonance', 'neutral', 'neutral', 'opposition', 'unexperienced'];
    emotions TEXT[] := ARRAY['empathy', 'trigger', 'insight', 'shock'];
    texts TEXT[] := ARRAY[
        '我也经历过类似的事情', '这让我想起了...', '说出了我想说的话',
        '突然被触动了', '原来不止我一个人这样', '有点意思', '不太认同',
        '没体验过这种感觉', '写得真好', '感同身受', '这正是我想说的',
        '突然被击中了', '原来别人也这样', '有种被理解的感觉',
        '这让我沉默了', '说出了心里话', '原来不止我一个人'
    ];
BEGIN
    FOR anchor_rec IN SELECT id FROM anchors LOOP
        FOR i IN 1..35 LOOP
            user_hash := hashes[1 + floor(random() * 5)::int];
            rt := types[1 + floor(random() * 7)::int];
            IF rt = 'resonance' THEN
                ew := emotions[1 + floor(random() * 4)::int];
            ELSE
                ew := NULL;
            END IF;
            txt := texts[1 + floor(random() * array_length(texts, 1))::int];
            rv := 0.3 + random() * 0.6;
            
            INSERT INTO reactions (user_id, anchor_id, reaction_type, emotion_word, modality, text_content, resonance_value)
            VALUES (
                (SELECT id FROM users WHERE phone_hash = user_hash),
                anchor_rec.id,
                rt,
                ew,
                'text',
                txt,
                round(rv::numeric, 3)
            );
        END LOOP;
    END LOOP;
END $$;
