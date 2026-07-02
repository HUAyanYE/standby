//! 路由单元测试

use standby_gateway::error::ApiError;
use standby_gateway::models::auth::{Claims, RegisterRequest, LoginRequest, AuthResponse};
use standby_gateway::models::SuccessResponse;

// ==================== 请求模型测试 ====================

#[test]
fn test_register_request_deserialization() {
    let json = r#"{"device_fingerprint": "test-device-123"}"#;
    let req: RegisterRequest = serde_json::from_str(json).unwrap();

    assert_eq!(req.device_fingerprint, "test-device-123");
}

#[test]
fn test_register_request_empty_fingerprint() {
    let json = r#"{"device_fingerprint": ""}"#;
    let req: RegisterRequest = serde_json::from_str(json).unwrap();

    assert!(req.device_fingerprint.is_empty());
}

#[test]
fn test_login_request_deserialization() {
    let json = r#"{"device_fingerprint": "test-device-456"}"#;
    let req: LoginRequest = serde_json::from_str(json).unwrap();

    assert_eq!(req.device_fingerprint, "test-device-456");
}

#[test]
fn test_auth_response_serialization() {
    let response = AuthResponse {
        token: "test-jwt-token".to_string(),
        user_id: "user-123".to_string(),
        expires_at: 4102444800,
    };

    let json = serde_json::to_string(&response).unwrap();
    assert!(json.contains("test-jwt-token"));
    assert!(json.contains("user-123"));
    assert!(json.contains("4102444800"));
}

#[test]
fn test_success_response_serialization() {
    let data = serde_json::json!({"key": "value"});
    let response = SuccessResponse::ok(data);

    let json = serde_json::to_string(&response).unwrap();
    assert!(json.contains("\"success\":true"));
    assert!(json.contains("\"key\":\"value\""));
}

// ==================== Claims 测试 ====================

#[test]
fn test_claims_creation() {
    let claims = Claims {
        sub: "user-123".to_string(),
        device_id: "device-456".to_string(),
        iat: 1000000000,
        exp: 4102444800,
    };

    assert_eq!(claims.sub, "user-123");
    assert_eq!(claims.device_id, "device-456");
    assert_eq!(claims.iat, 1000000000);
    assert_eq!(claims.exp, 4102444800);
}

#[test]
fn test_claims_clone() {
    let claims = Claims {
        sub: "user-123".to_string(),
        device_id: "device-456".to_string(),
        iat: 1000000000,
        exp: 4102444800,
    };

    let cloned = claims.clone();
    assert_eq!(claims.sub, cloned.sub);
    assert_eq!(claims.device_id, cloned.device_id);
}

// ==================== 错误响应格式测试 ====================

#[test]
fn test_unauthorized_error_message() {
    let error = ApiError::Unauthorized("missing token".into());
    let message = error.to_string();

    assert!(message.contains("未认证"));
    assert!(message.contains("missing token"));
}

#[test]
fn test_bad_request_error_message() {
    let error = ApiError::BadRequest("invalid input".into());
    let message = error.to_string();

    assert!(message.contains("请求参数错误"));
    assert!(message.contains("invalid input"));
}

#[test]
fn test_not_found_error_message() {
    let error = ApiError::NotFound("resource not found".into());
    let message = error.to_string();

    assert!(message.contains("资源不存在"));
    assert!(message.contains("resource not found"));
}

#[test]
fn test_engine_error_message() {
    let error = ApiError::EngineError("service unavailable".into());
    let message = error.to_string();

    assert!(message.contains("引擎调用失败"));
    assert!(message.contains("service unavailable"));
}
