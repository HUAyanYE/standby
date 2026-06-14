-- Migration 002: Users table
-- 设计原则: 不存储任何 PII, 只有设备指纹哈希

CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_hash          TEXT UNIQUE,
    internal_token      TEXT UNIQUE NOT NULL,
    device_fingerprint  TEXT NOT NULL,
    marker_credit       REAL NOT NULL DEFAULT 0.5,
    trust_level         SMALLINT NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_internal_token ON users(internal_token);
CREATE INDEX IF NOT EXISTS idx_users_device_fingerprint ON users(device_fingerprint);
