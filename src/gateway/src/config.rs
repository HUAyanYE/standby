// 网关配置
use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct GatewayConfig {
    pub port: u16,
    pub jwt_secret: String,
    pub jwt_expiry_hours: u64,
    
    // 引擎 gRPC 地址
    pub engines: EngineEndpoints,
    
    // NATS
    pub nats_url: String,
    
    // 速率限制
    pub rate_limit: RateLimitConfig,
}

#[derive(Debug, Clone, Deserialize)]
pub struct EngineEndpoints {
    pub resonance: String,   // "http://localhost:8091"
    pub anchor: String,      // "http://localhost:8090"
    pub governance: String,  // "http://localhost:8092"
    pub user: String,        // "http://localhost:8093"
    pub context: String,     // "http://localhost:8094"
}

#[derive(Debug, Clone, Deserialize)]
pub struct RateLimitConfig {
    pub requests_per_minute: u32,
    pub burst: u32,
}

impl GatewayConfig {
    pub fn load() -> anyhow::Result<Self> {
        // 默认配置
        let config = Self {
            port: std::env::var("GATEWAY_PORT")
                .unwrap_or_else(|_| "8080".to_string())
                .parse()?,
            jwt_secret: std::env::var("JWT_SECRET")
                .unwrap_or_else(|_| "dev-secret-change-in-production".to_string()),
            jwt_expiry_hours: 24,
            engines: EngineEndpoints {
                resonance: std::env::var("ENGINE_RESONANCE")
                    .unwrap_or_else(|_| "http://localhost:8091".to_string()),
                anchor: std::env::var("ENGINE_ANCHOR")
                    .unwrap_or_else(|_| "http://localhost:8090".to_string()),
                governance: std::env::var("ENGINE_GOVERNANCE")
                    .unwrap_or_else(|_| "http://localhost:8092".to_string()),
                user: std::env::var("ENGINE_USER")
                    .unwrap_or_else(|_| "http://localhost:8093".to_string()),
                context: std::env::var("ENGINE_CONTEXT")
                    .unwrap_or_else(|_| "http://localhost:8094".to_string()),
            },
            nats_url: std::env::var("NATS_URL")
                .unwrap_or_else(|_| "nats://localhost:4222".to_string()),
            rate_limit: RateLimitConfig {
                requests_per_minute: 600,
                burst: 10,
            },
        };
        Ok(config)
    }
}
