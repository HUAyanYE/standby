// 应用状态
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

use crate::config::GatewayConfig;
use crate::proto::engines::{
    AnchorEngineClient, ContextEngineClient,
    GovernanceEngineClient, ResonanceEngineClient,
    UserEngineClient,
};

/// 应用全局状态
pub struct AppState {
    pub config: GatewayConfig,

    // gRPC 客户端
    pub resonance_client: ResonanceEngineClient<tonic::transport::Channel>,
    pub governance_client: GovernanceEngineClient<tonic::transport::Channel>,
    pub anchor_client: AnchorEngineClient<tonic::transport::Channel>,
    pub user_client: UserEngineClient<tonic::transport::Channel>,
    pub context_client: ContextEngineClient<tonic::transport::Channel>,

    // 速率限制器 (token bucket per device)
    pub rate_limiter: Arc<RwLock<HashMap<String, TokenBucket>>>,

    // JWT 黑名单
    pub token_blacklist: Arc<RwLock<std::collections::HashSet<String>>>,

    // 设备指纹缓存
    pub device_cache: Arc<RwLock<HashMap<String, DeviceInfo>>>,
}

/// Token Bucket 速率限制器
pub struct TokenBucket {
    pub tokens: f64,
    pub last_refill: u64,
    pub max_tokens: f64,
    pub refill_rate: f64,
}

impl TokenBucket {
    pub fn new(max_tokens: u32, refill_rate: f64) -> Self {
        Self {
            tokens: max_tokens as f64,
            last_refill: current_timestamp(),
            max_tokens: max_tokens as f64,
            refill_rate,
        }
    }

    pub fn try_consume(&mut self) -> bool {
        self.refill();
        if self.tokens >= 1.0 {
            self.tokens -= 1.0;
            true
        } else {
            false
        }
    }

    fn refill(&mut self) {
        let now = current_timestamp();
        let elapsed = (now - self.last_refill) as f64 / 1000.0;
        self.tokens = (self.tokens + elapsed * self.refill_rate).min(self.max_tokens);
        self.last_refill = now;
    }
}

/// 设备信息 (缓存)
#[derive(Clone)]
pub struct DeviceInfo {
    pub device_hash: String,
    pub user_id: String,
    pub is_valid: bool,
    pub last_seen: u64,
}

fn current_timestamp() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_millis() as u64
}

impl AppState {
    pub async fn new(config: GatewayConfig) -> anyhow::Result<Self> {
        // 带重试的 gRPC 连接 — 等待引擎就绪
        let max_retries = 30;
        let retry_delay = std::time::Duration::from_secs(2);

        let mut resonance_client = None;
        let mut governance_client = None;
        let mut anchor_client = None;
        let mut user_client = None;
        let mut context_client = None;

        for attempt in 1..=max_retries {
            tracing::info!("连接引擎 (尝试 {}/{})...", attempt, max_retries);

            // 先检查所有连接结果
            let r_res = ResonanceEngineClient::connect(config.engines.resonance.clone()).await;
            let g_res = GovernanceEngineClient::connect(config.engines.governance.clone()).await;
            let a_res = AnchorEngineClient::connect(config.engines.anchor.clone()).await;
            let u_res = UserEngineClient::connect(config.engines.user.clone()).await;
            let c_res = ContextEngineClient::connect(config.engines.context.clone()).await;

            if r_res.is_ok() && g_res.is_ok() && a_res.is_ok() && u_res.is_ok() && c_res.is_ok() {
                resonance_client = Some(r_res.unwrap());
                governance_client = Some(g_res.unwrap());
                anchor_client = Some(a_res.unwrap());
                user_client = Some(u_res.unwrap());
                context_client = Some(c_res.unwrap());
                tracing::info!("所有引擎连接成功");
                break;
            }

            if attempt == max_retries {
                anyhow::bail!("引擎连接超时 ({} 次尝试)", max_retries);
            }

            let mut errors = Vec::new();
            if let Err(e) = &r_res { errors.push(format!("共鸣: {}", e)); }
            if let Err(e) = &g_res { errors.push(format!("治理: {}", e)); }
            if let Err(e) = &a_res { errors.push(format!("锚点: {}", e)); }
            if let Err(e) = &u_res { errors.push(format!("用户: {}", e)); }
            if let Err(e) = &c_res { errors.push(format!("情境: {}", e)); }

            tracing::warn!("引擎未就绪: {}，{}s 后重试", errors.join(", "), retry_delay.as_secs());
            tokio::time::sleep(retry_delay).await;
        }

        // 安全 unwrap（循环保证已初始化）
        let resonance_client = resonance_client.expect("resonance_client");
        let governance_client = governance_client.expect("governance_client");
        let anchor_client = anchor_client.expect("anchor_client");
        let user_client = user_client.expect("user_client");
        let context_client = context_client.expect("context_client");

        tracing::info!("gRPC 客户端已连接:");
        tracing::info!("  共鸣引擎: {}", config.engines.resonance);
        tracing::info!("  治理引擎: {}", config.engines.governance);
        tracing::info!("  锚点引擎: {}", config.engines.anchor);
        tracing::info!("  用户引擎: {}", config.engines.user);
        tracing::info!("  情境引擎: {}", config.engines.context);

        Ok(Self {
            config,
            resonance_client,
            governance_client,
            anchor_client,
            user_client,
            context_client,
            rate_limiter: Arc::new(RwLock::new(HashMap::new())),
            token_blacklist: Arc::new(RwLock::new(std::collections::HashSet::new())),
            device_cache: Arc::new(RwLock::new(HashMap::new())),
        })
    }

    /// 获取或创建速率限制桶
    pub async fn get_or_create_bucket(&self, key: &str) -> bool {
        let mut limiters = self.rate_limiter.write().await;
        let bucket = limiters.entry(key.to_string()).or_insert_with(|| {
            TokenBucket::new(
                self.config.rate_limit.burst,
                self.config.rate_limit.requests_per_minute as f64 / 60.0,
            )
        });
        bucket.try_consume()
    }
}
