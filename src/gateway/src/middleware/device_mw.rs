// 设备指纹中间件
use axum::{
    body::Body,
    extract::State,
    http::{Request, StatusCode},
    middleware::Next,
    response::Response,
};
use std::sync::Arc;

use crate::state::AppState;

/// 设备指纹验证中间件
pub async fn verify_device(
    State(state): State<Arc<AppState>>,
    mut req: Request<Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    let device_fp = req
        .headers()
        .get("X-Device-Fingerprint")
        .and_then(|v| v.to_str().ok())
        .ok_or(StatusCode::BAD_REQUEST)?
        .to_string();

    if device_fp.len() != 64 || !device_fp.chars().all(|c| c.is_ascii_hexdigit()) {
        return Err(StatusCode::BAD_REQUEST);
    }

    let mut cache = state.device_cache.write().await;
    cache.insert(
        device_fp.clone(),
        crate::state::DeviceInfo {
            device_hash: device_fp.clone(),
            user_id: String::new(),
            is_valid: true,
            last_seen: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_millis() as u64,
        },
    );

    // 设置设备哈希到请求扩展
    req.extensions_mut().insert(device_fp);

    Ok(next.run(req).await)
}
