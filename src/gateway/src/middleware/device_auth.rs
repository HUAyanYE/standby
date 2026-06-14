use axum::extract::{Request, State};
use axum::http::HeaderMap;
use axum::middleware::Next;
use axum::response::Response;
use base64::Engine;
use base64::engine::general_purpose::STANDARD as BASE64;
use chrono::Utc;
use hmac::{Hmac, Mac};
use sha2::Sha256;

use crate::error::ApiError;
use crate::models::auth::Claims;
use crate::AppState;

type HmacSha256 = Hmac<Sha256>;

const DEVICE_ID_HEADER: &str = "x-device-id";
const DEVICE_SIGNATURE_HEADER: &str = "x-device-signature";
const TIMESTAMP_HEADER: &str = "x-request-timestamp";
const TIMESTAMP_WINDOW_SECS: i64 = 300; // 5 分钟

/// 设备认证中间件
///
/// 验证请求签名: HMAC-SHA256(device_secret, method + path + timestamp + device_id)
/// 防重放: 时间戳窗口 ±5 分钟
pub async fn device_auth(
    State(state): State<AppState>,
    request: Request,
    next: Next,
) -> Result<Response, ApiError> {
    let headers = request.headers().clone();

    // 白名单路由跳过设备认证
    let path = request.uri().path();
    if is_device_auth_exempt(path) {
        return Ok(next.run(request).await);
    }

    // 提取设备 ID
    let device_id = get_header_value(&headers, DEVICE_ID_HEADER)?;

    // 提取签名
    let signature = get_header_value(&headers, DEVICE_SIGNATURE_HEADER)?;

    // 提取并验证时间戳
    let timestamp_str = get_header_value(&headers, TIMESTAMP_HEADER)?;
    let timestamp: i64 = timestamp_str
        .parse()
        .map_err(|_| ApiError::BadRequest("无效的时间戳".into()))?;

    let now = Utc::now().timestamp();
    if (now - timestamp).abs() > TIMESTAMP_WINDOW_SECS {
        return Err(ApiError::Unauthorized("请求已过期或时间戳无效".into()));
    }

    // 从扩展中获取 Claims (JWT 中间件已注入)
    // 如果没有 Claims，说明是未认证请求，跳过签名验证
    if let Some(claims) = request.extensions().get::<Claims>() {
        // 验证签名 — 使用配置中的 device_secret 而非 device_id
        let method = request.method().as_str();
        let path = request.uri().path();

        let message = format!("{}{}{}{}", method, path, timestamp_str, device_id);
        let expected_signature = compute_hmac(&state.config.device_secret, &message);

        if signature != expected_signature {
            return Err(ApiError::Unauthorized("设备签名验证失败".into()));
        }
    }

    Ok(next.run(request).await)
}

/// 计算 HMAC-SHA256
pub fn compute_hmac(secret: &str, message: &str) -> String {
    let mut mac =
        HmacSha256::new_from_slice(secret.as_bytes()).expect("HMAC 可以接受任意长度的密钥");
    mac.update(message.as_bytes());
    let result = mac.finalize();
    BASE64.encode(result.into_bytes())
}

/// 提取头信息值
fn get_header_value(headers: &HeaderMap, name: &str) -> Result<String, ApiError> {
    headers
        .get(name)
        .and_then(|v| v.to_str().ok())
        .map(|s| s.to_string())
        .ok_or_else(|| ApiError::Unauthorized(format!("缺少 {} 头", name)))
}

/// 设备认证白名单路由
/// 仅健康检查和认证路由跳过设备认证（注册/登录时用户尚未认证）
fn is_device_auth_exempt(path: &str) -> bool {
    matches!(
        path,
        "/health"
            | "/api/v1/auth/register"
            | "/api/v1/auth/login"
    )
}
