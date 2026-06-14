use std::env;

/// 网关配置 — 从环境变量加载
#[derive(Debug, Clone)]
pub struct GatewayConfig {
    pub port: u16,
    pub jwt_secret: String,
    pub jwt_expiry_hours: u64,
    pub device_secret: String,
    pub engine_anchor_url: String,
    pub engine_resonance_url: String,
    pub engine_governance_url: String,
    pub engine_context_url: String,
    pub rate_limit_per_minute: u32,
    pub log_level: String,
    pub request_timeout_secs: u64,
}

impl GatewayConfig {
    pub fn from_env() -> anyhow::Result<Self> {
        dotenvy::dotenv().ok();

        Ok(Self {
            port: env::var("GATEWAY_PORT")
                .unwrap_or_else(|_| "8080".into())
                .parse()?,
            jwt_secret: env::var("JWT_SECRET")
                .map_err(|_| anyhow::anyhow!("JWT_SECRET 环境变量必须设置"))?,
            jwt_expiry_hours: env::var("JWT_EXPIRY_HOURS")
                .unwrap_or_else(|_| "24".into())
                .parse()?,
            device_secret: env::var("DEVICE_SECRET")
                .unwrap_or_else(|_| {
                    tracing::warn!("DEVICE_SECRET 未设置，使用 JWT_SECRET 作为回退");
                    env::var("JWT_SECRET").unwrap_or_default()
                }),
            engine_anchor_url: env::var("ENGINE_ANCHOR_URL")
                .unwrap_or_else(|_| "http://localhost:8090".into()),
            engine_resonance_url: env::var("ENGINE_RESONANCE_URL")
                .unwrap_or_else(|_| "http://localhost:8091".into()),
            engine_governance_url: env::var("ENGINE_GOVERNANCE_URL")
                .unwrap_or_else(|_| "http://localhost:8092".into()),
            engine_context_url: env::var("ENGINE_CONTEXT_URL")
                .unwrap_or_else(|_| "http://localhost:8094".into()),
            rate_limit_per_minute: env::var("RATE_LIMIT_PER_MINUTE")
                .unwrap_or_else(|_| "60".into())
                .parse()?,
            log_level: env::var("LOG_LEVEL")
                .unwrap_or_else(|_| "info".into()),
            request_timeout_secs: env::var("REQUEST_TIMEOUT_SECS")
                .unwrap_or_else(|_| "30".into())
                .parse()?,
        })
    }
}
