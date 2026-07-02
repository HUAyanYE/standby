//! 中间件单元测试

use standby_gateway::error::ApiError;
use standby_gateway::middleware::device_auth;
use standby_gateway::models::auth::Claims;

/// 创建测试用的 JWT token
fn create_test_token(secret: &str, sub: &str, device_id: &str, exp: u64) -> String {
    use jsonwebtoken::{encode, EncodingKey, Header};
    let claims = Claims {
        sub: sub.to_string(),
        device_id: device_id.to_string(),
        iat: 1000000000,
        exp,
    };
    encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(secret.as_bytes()),
    )
    .unwrap()
}

// ==================== HMAC 计算测试 ====================

#[test]
fn test_compute_hmac_deterministic() {
    let secret = "test-secret";
    let message = "GET/api/test1234567890device123";

    let signature1 = device_auth::compute_hmac(secret, message);
    let signature2 = device_auth::compute_hmac(secret, message);

    // 相同输入应该产生相同输出
    assert_eq!(signature1, signature2);
}

#[test]
fn test_compute_hmac_different_message() {
    let secret = "test-secret";
    let message1 = "GET/api/test1234567890device123";
    let message2 = "POST/api/test1234567890device123";

    let signature1 = device_auth::compute_hmac(secret, message1);
    let signature2 = device_auth::compute_hmac(secret, message2);

    // 不同输入应该产生不同输出
    assert_ne!(signature1, signature2);
}

#[test]
fn test_compute_hmac_different_secret() {
    let secret1 = "test-secret-1";
    let secret2 = "test-secret-2";
    let message = "GET/api/test1234567890device123";

    let signature1 = device_auth::compute_hmac(secret1, message);
    let signature2 = device_auth::compute_hmac(secret2, message);

    // 不同密钥应该产生不同输出
    assert_ne!(signature1, signature2);
}

#[test]
fn test_compute_hmac_base64_encoded() {
    let secret = "test-secret";
    let message = "test-message";

    let signature = device_auth::compute_hmac(secret, message);

    // 结果应该是有效的 base64
    assert!(base64::Engine::decode(&base64::engine::general_purpose::STANDARD, &signature).is_ok());
}

#[test]
fn test_compute_hmac_empty_inputs() {
    let secret = "";
    let message = "";

    let signature = device_auth::compute_hmac(secret, message);

    // 空输入也应该产生有效输出
    assert!(!signature.is_empty());
}

// ==================== JWT Token 创建测试 ====================

#[test]
fn test_create_valid_token() {
    let secret = "test-secret";
    let token = create_test_token(secret, "user123", "device123", 4102444800);

    // Token 应该是非空的
    assert!(!token.is_empty());

    // Token 应该包含三个部分（header.payload.signature）
    let parts: Vec<&str> = token.split('.').collect();
    assert_eq!(parts.len(), 3);
}

#[test]
fn test_create_expired_token() {
    let secret = "test-secret";
    let token = create_test_token(secret, "user123", "device123", 1000000000);

    // Token 应该是非空的
    assert!(!token.is_empty());
}

// ==================== Claims 测试 ====================

#[test]
fn test_claims_serialization() {
    let claims = Claims {
        sub: "user123".to_string(),
        device_id: "device456".to_string(),
        iat: 1000000000,
        exp: 4102444800,
    };

    let json = serde_json::to_string(&claims).unwrap();
    assert!(json.contains("user123"));
    assert!(json.contains("device456"));
}

#[test]
fn test_claims_deserialization() {
    let json = r#"{"sub":"user123","device_id":"device456","iat":1000000000,"exp":4102444800}"#;
    let claims: Claims = serde_json::from_str(json).unwrap();

    assert_eq!(claims.sub, "user123");
    assert_eq!(claims.device_id, "device456");
    assert_eq!(claims.iat, 1000000000);
    assert_eq!(claims.exp, 4102444800);
}

// ==================== 错误类型测试 ====================

#[test]
fn test_api_error_display() {
    let error = ApiError::Unauthorized("test".into());
    assert_eq!(error.to_string(), "未认证: test");

    let error = ApiError::Forbidden("test".into());
    assert_eq!(error.to_string(), "禁止访问: test");

    let error = ApiError::NotFound("test".into());
    assert_eq!(error.to_string(), "资源不存在: test");

    let error = ApiError::BadRequest("test".into());
    assert_eq!(error.to_string(), "请求参数错误: test");

    let error = ApiError::RateLimited;
    assert_eq!(error.to_string(), "请求过于频繁，请稍后重试");

    let error = ApiError::EngineError("test".into());
    assert_eq!(error.to_string(), "引擎调用失败: test");

    let error = ApiError::Internal("test".into());
    assert_eq!(error.to_string(), "内部错误: test");
}
