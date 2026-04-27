// 认证处理器
use axum::{extract::State, Json};
use std::sync::Arc;

use crate::{
    auth::{self, AuthResponse, DeviceAuthRequest},
    state::AppState,
};

/// 设备认证 — 注册/登录
pub async fn device_auth(
    State(state): State<Arc<AppState>>,
    Json(req): Json<DeviceAuthRequest>,
) -> Json<AuthResponse> {
    tracing::info!("设备认证请求: device_type={}, fp={}...",
        req.device_type, &req.device_fingerprint[..8]);
    
    // 验证设备指纹格式
    if req.device_fingerprint.len() != 64 {
        return Json(AuthResponse {
            success: false,
            access_token: None,
            refresh_token: None,
            expires_at: None,
            user_id: None,
            error: Some("无效的设备指纹".to_string()),
        });
    }
    
    // TODO: 查询/创建用户 (需要 User Engine)
    // 暂时用设备指纹的 hash 作为 user_id
    let user_id = format!("user_{}", &req.device_fingerprint[..16]);
    
    // 生成 token
    let access_token = auth::generate_token(
        &user_id,
        &req.device_fingerprint,
        &state.config.jwt_secret,
        1,  // 1 小时
        "access",
    ).unwrap();
    
    let refresh_token = auth::generate_token(
        &user_id,
        &req.device_fingerprint,
        &state.config.jwt_secret,
        state.config.jwt_expiry_hours,
        "refresh",
    ).unwrap();
    
    let expires_at = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() + 3600;
    
    Json(AuthResponse {
        success: true,
        access_token: Some(access_token),
        refresh_token: Some(refresh_token),
        expires_at: Some(expires_at),
        user_id: Some(user_id),
        error: None,
    })
}

/// 刷新令牌
pub async fn refresh_token(
    State(state): State<Arc<AppState>>,
    Json(req): Json<DeviceAuthRequest>,
) -> Json<AuthResponse> {
    let refresh = match req.existing_token {
        Some(t) => t,
        None => return Json(AuthResponse {
            success: false,
            access_token: None,
            refresh_token: None,
            expires_at: None,
            user_id: None,
            error: Some("缺少刷新令牌".to_string()),
        }),
    };
    
    let response = auth::refresh_token(
        &refresh,
        &req.device_fingerprint,
        &state.config.jwt_secret,
        state.config.jwt_expiry_hours,
    ).unwrap_or_else(|_| AuthResponse {
        success: false,
        access_token: None,
        refresh_token: None,
        expires_at: None,
        user_id: None,
        error: Some("刷新失败".to_string()),
    });
    
    Json(response)
}
