use serde::{Deserialize, Serialize};

/// JWT Claims
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,        // user_id
    pub device_id: String,  // 设备指纹哈希
    pub iat: u64,           // 签发时间
    pub exp: u64,           // 过期时间
}

/// 注册请求
#[derive(Debug, Deserialize)]
pub struct RegisterRequest {
    pub device_fingerprint: String,
}

/// 登录请求
#[derive(Debug, Deserialize)]
pub struct LoginRequest {
    pub device_fingerprint: String,
}

/// 认证响应
#[derive(Debug, Serialize)]
pub struct AuthResponse {
    pub token: String,
    pub user_id: String,
    pub expires_at: u64,
}
