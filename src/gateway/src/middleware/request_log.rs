use axum::extract::{Request, State};
use axum::middleware::Next;
use axum::response::Response;
use tracing::info;

use crate::AppState;

/// 请求日志中间件
///
/// 记录: request_id、方法、路径、状态码、耗时、设备 ID
pub async fn request_log(
    State(_state): State<AppState>,
    mut request: Request,
    next: Next,
) -> Response {
    let request_id = uuid::Uuid::new_v4().to_string();
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

    // 将 request_id 注入请求扩展，供后续中间件和处理器使用
    request.extensions_mut().insert(request_id.clone());

    let start = std::time::Instant::now();
    let response = next.run(request).await;
    let duration = start.elapsed();

    let status = response.status().as_u16();

    info!(
        request_id = %request_id,
        method = %method,
        path = %path,
        status = status,
        duration_ms = duration.as_millis() as u64,
        device_id = %device_id,
        "请求处理完成"
    );

    response
}
