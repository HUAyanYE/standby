-- Migration 008: User contexts table
-- 端侧上报的用户当前情境状态

CREATE TABLE IF NOT EXISTS user_contexts (
    user_id             TEXT PRIMARY KEY,
    scene_type          TEXT NOT NULL DEFAULT '',
    mood_hint           TEXT NOT NULL DEFAULT '',
    attention_level     TEXT NOT NULL DEFAULT '',
    device              SMALLINT NOT NULL DEFAULT 0,
    context_timestamp   BIGINT NOT NULL DEFAULT 0,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
