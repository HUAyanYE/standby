use std::time::Duration;
use tonic::Code;

use crate::error::ApiError;

/// 重试配置
pub struct RetryConfig {
    pub max_retries: u32,
    pub base_delay: Duration,
    pub max_delay: Duration,
}

impl Default for RetryConfig {
    fn default() -> Self {
        Self {
            max_retries: 2,
            base_delay: Duration::from_millis(100),
            max_delay: Duration::from_secs(2),
        }
    }
}

/// 判断 gRPC 错误是否可重试
fn is_retryable(code: Code) -> bool {
    matches!(
        code,
        Code::Unavailable | Code::DeadlineExceeded | Code::ResourceExhausted | Code::Internal
    )
}

/// 带重试的 gRPC 调用
///
/// 对暂时性错误 (Unavailable, DeadlineExceeded) 进行指数退避重试。
pub async fn with_retry<F, Fut, T>(
    config: &RetryConfig,
    operation_name: &str,
    mut f: F,
) -> Result<T, ApiError>
where
    F: FnMut() -> Fut,
    Fut: std::future::Future<Output = Result<T, tonic::Status>>,
{
    let mut last_error = None;

    for attempt in 0..=config.max_retries {
        match f().await {
            Ok(result) => return Ok(result),
            Err(status) => {
                if is_retryable(status.code()) && attempt < config.max_retries {
                    let delay = std::cmp::min(
                        config.base_delay * 2u32.pow(attempt),
                        config.max_delay,
                    );
                    tracing::warn!(
                        operation = operation_name,
                        attempt = attempt + 1,
                        delay_ms = delay.as_millis() as u64,
                        error = %status.message(),
                        "gRPC 调用失败，准备重试"
                    );
                    tokio::time::sleep(delay).await;
                    last_error = Some(status);
                } else {
                    return Err(status.into());
                }
            }
        }
    }

    // 所有重试都失败
    Err(last_error.unwrap().into())
}

/// 带超时的 gRPC 调用
pub async fn with_timeout<F, Fut, T>(
    timeout: Duration,
    operation_name: &str,
    f: F,
) -> Result<T, ApiError>
where
    F: FnOnce() -> Fut,
    Fut: std::future::Future<Output = Result<T, tonic::Status>>,
{
    match tokio::time::timeout(timeout, f()).await {
        Ok(result) => result.map_err(|e| e.into()),
        Err(_) => {
            tracing::error!(
                operation = operation_name,
                timeout_ms = timeout.as_millis() as u64,
                "gRPC 调用超时"
            );
            Err(ApiError::EngineError(format!(
                "引擎调用超时 ({}ms)",
                timeout.as_millis()
            )))
        }
    }
}
