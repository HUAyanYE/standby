use axum::extract::{Request, State};
use axum::middleware::Next;
use axum::response::Response;
use tracing::info;

use crate::AppState;

/// 请求日志中间件
///
/// 记录: 方法、路径、状态码、耗时、设备 ID
pub async fn request_log(
    State(_state): State<AppState>,
    request: Request,
    next: Next,
) -> Response {
    let method = request.method().clone();
    let uri = request.uri().clone();
    let path = uri.path().to_string();

    // 提取设备 ID
    let device_id = request
        .headers()
        .get("x-device-id")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("-")
        .to_string();

    let start = std::time::Instant::now();
    let response = next.run(request).await;
    let duration = start.elapsed();

    let status = response.status().as_u16();

    info!(
        method = %method,
        path = %path,
        status = status,
        duration_ms = duration.as_millis() as u64,
        device_id = %device_id,
        "请求处理完成"
    );

    response
}
