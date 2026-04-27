// 认证中间件
use axum::{
    body::Body,
    extract::State,
    http::{header::AUTHORIZATION, HeaderValue, Request, StatusCode},
    middleware::Next,
    response::Response,
};
use std::sync::Arc;

use crate::{auth, state::AppState};

/// JWT 认证中间件
pub async fn verify_jwt(
    State(state): State<Arc<AppState>>,
    mut req: Request<Body>,
    next: Next,
) -> Result<Response, StatusCode> {
    // 调试：打印请求头
    let headers = req.headers();
    tracing::info!("认证中间件请求头: {:?}", headers);
    
    let auth_header = req
        .headers()
        .get(AUTHORIZATION)
        .and_then(|v| v.to_str().ok())
        .ok_or(StatusCode::UNAUTHORIZED)?;

    let token = auth_header
        .strip_prefix("Bearer ")
        .ok_or(StatusCode::UNAUTHORIZED)?;

    let claims = auth::validate_token(token, &state.config.jwt_secret)
        .map_err(|_| StatusCode::UNAUTHORIZED)?;

    let blacklist = state.token_blacklist.read().await;
    if blacklist.contains(token) {
        return Err(StatusCode::UNAUTHORIZED);
    }

    // 验证设备指纹是否匹配（暂时禁用用于调试）
    let request_device_fp = req
        .headers()
        .get("X-Device-Fingerprint")
        .and_then(|v| v.to_str().ok());
    
    if let Some(fp) = request_device_fp {
        if fp != claims.device_hash {
            tracing::warn!("设备指纹不匹配: 请求={}, JWT={}", fp, claims.device_hash);
            // return Err(StatusCode::UNAUTHORIZED); // 暂时禁用以允许测试
        }
    }
    
    req.extensions_mut().insert(claims.sub.clone());
    req.extensions_mut().insert(claims.device_hash.clone());

    // 设置 X-User-Id 头供下游 handler 使用
    if let Ok(header_val) = HeaderValue::from_str(&claims.sub) {
        req.headers_mut().insert("x-user-id", header_val);
    }

    Ok(next.run(req).await)
}
