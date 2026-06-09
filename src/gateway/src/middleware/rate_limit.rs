use std::sync::Arc;
use std::time::{Duration, Instant};

use axum::extract::{Request, State};
use axum::http::header;
use axum::middleware::Next;
use axum::response::Response;
use dashmap::DashMap;

use crate::error::ApiError;
use crate::models::auth::Claims;

/// 滑动窗口速率限制器
#[derive(Clone)]
pub struct RateLimiter {
    /// device_id → (窗口开始时间, 请求计数)
    counters: Arc<DashMap<String, (Instant, u32)>>,
    max_requests: u32,
    window: Duration,
}

impl RateLimiter {
    pub fn new(max_requests_per_minute: u32) -> Self {
        Self {
            counters: Arc::new(DashMap::new()),
            max_requests: max_requests_per_minute,
            window: Duration::from_secs(60),
        }
    }

    /// 检查是否超过速率限制
    fn check(&self, key: &str) -> bool {
        let now = Instant::now();
        let mut entry = self.counters.entry(key.to_string()).or_insert((now, 0));

        let (window_start, count) = entry.value_mut();

        // 窗口过期，重置
        if now.duration_since(*window_start) > self.window {
            *window_start = now;
            *count = 1;
            return true;
        }

        if *count >= self.max_requests {
            return false;
        }

        *count += 1;
        true
    }

    /// 清理过期条目 (定期调用)
    pub fn cleanup(&self) {
        let now = Instant::now();
        self.counters.retain(|_, (start, _)| {
            now.duration_since(*start) <= self.window * 2
        });
    }
}

/// 速率限制中间件
pub async fn rate_limit(
    State(rate_limiter): State<Arc<RateLimiter>>,
    request: Request,
    next: Next,
) -> Result<Response, ApiError> {
    // 从 Claims 中获取 device_id，或使用 IP 作为 fallback
    let key = request
        .extensions()
        .get::<Claims>()
        .map(|c| c.device_id.clone())
        .unwrap_or_else(|| {
            request
                .headers()
                .get(header::FORWARDED)
                .and_then(|v| v.to_str().ok())
                .unwrap_or("unknown")
                .to_string()
        });

    if !rate_limiter.check(&key) {
        return Err(ApiError::RateLimited);
    }

    Ok(next.run(request).await)
}
