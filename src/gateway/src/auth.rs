// JWT 认证
use jsonwebtoken::{decode, encode, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};

/// JWT Claims
#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    /// 用户 ID
    pub sub: String,
    /// 设备指纹哈希
    pub device_hash: String,
    /// 签发时间
    pub iat: u64,
    /// 过期时间
    pub exp: u64,
    /// 令牌类型: "access" / "refresh"
    pub token_type: String,
}

/// 认证请求
#[derive(Debug, Deserialize)]
pub struct DeviceAuthRequest {
    pub device_type: String,      // "phone" / "tablet" / "pc" / "vehicle"
    pub device_fingerprint: String, // SHA-256 哈希
    pub os_version: String,
    pub app_version: String,
    pub phone_number_hash: Option<String>,  // 注册时
    pub verification_code: Option<String>,  // 注册时
    pub existing_token: Option<String>,     // 刷新时
}

/// 认证响应
#[derive(Debug, Serialize)]
pub struct AuthResponse {
    pub success: bool,
    pub access_token: Option<String>,
    pub refresh_token: Option<String>,
    pub expires_at: Option<u64>,
    pub user_id: Option<String>,
    pub error: Option<String>,
}

/// 生成 JWT token
pub fn generate_token(
    user_id: &str,
    device_hash: &str,
    secret: &str,
    expiry_hours: u64,
    token_type: &str,
) -> anyhow::Result<String> {
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)?
        .as_secs();
    
    let claims = Claims {
        sub: user_id.to_string(),
        device_hash: device_hash.to_string(),
        iat: now,
        exp: now + expiry_hours * 3600,
        token_type: token_type.to_string(),
    };
    
    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )?;
    
    Ok(token)
}

/// 验证 JWT token
pub fn validate_token(token: &str, secret: &str) -> anyhow::Result<Claims> {
    let decoded = decode::<Claims>(
        token,
        &DecodingKey::from_secret(secret.as_bytes()),
        &Validation::default(),
    )?;
    
    Ok(decoded.claims)
}

/// 刷新 token
pub fn refresh_token(
    refresh_token: &str,
    device_hash: &str,
    secret: &str,
    expiry_hours: u64,
) -> anyhow::Result<AuthResponse> {
    // 验证 refresh token
    let claims = validate_token(refresh_token, secret)?;
    
    if claims.token_type != "refresh" {
        return Ok(AuthResponse {
            success: false,
            access_token: None,
            refresh_token: None,
            expires_at: None,
            user_id: None,
            error: Some("无效的刷新令牌".to_string()),
        });
    }
    
    // 验证设备指纹
    if claims.device_hash != device_hash {
        return Ok(AuthResponse {
            success: false,
            access_token: None,
            refresh_token: None,
            expires_at: None,
            user_id: None,
            error: Some("设备指纹不匹配".to_string()),
        });
    }
    
    // 生成新 token
    let access = generate_token(&claims.sub, device_hash, secret, 1, "access")?;
    let exp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)?
        .as_secs() + expiry_hours * 3600;
    
    Ok(AuthResponse {
        success: true,
        access_token: Some(access),
        refresh_token: None,
        expires_at: Some(exp),
        user_id: Some(claims.sub),
        error: None,
    })
}
