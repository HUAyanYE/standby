//! ApiError 单元测试

use standby_gateway::error::ApiError;

#[test]
fn test_unauthorized_display() {
    let error = ApiError::Unauthorized("invalid token".into());
    assert_eq!(error.to_string(), "未认证: invalid token");
}

#[test]
fn test_forbidden_display() {
    let error = ApiError::Forbidden("no access".into());
    assert_eq!(error.to_string(), "禁止访问: no access");
}

#[test]
fn test_not_found_display() {
    let error = ApiError::NotFound("resource missing".into());
    assert_eq!(error.to_string(), "资源不存在: resource missing");
}

#[test]
fn test_bad_request_display() {
    let error = ApiError::BadRequest("invalid input".into());
    assert_eq!(error.to_string(), "请求参数错误: invalid input");
}

#[test]
fn test_rate_limited_display() {
    let error = ApiError::RateLimited;
    assert_eq!(error.to_string(), "请求过于频繁，请稍后重试");
}

#[test]
fn test_engine_error_display() {
    let error = ApiError::EngineError("service down".into());
    assert_eq!(error.to_string(), "引擎调用失败: service down");
}

#[test]
fn test_internal_error_display() {
    let error = ApiError::Internal("something went wrong".into());
    assert_eq!(error.to_string(), "内部错误: something went wrong");
}

#[test]
fn test_error_debug_format() {
    let error = ApiError::Unauthorized("test".into());
    let debug_str = format!("{:?}", error);

    assert!(debug_str.contains("Unauthorized"));
    assert!(debug_str.contains("test"));
}

#[test]
fn test_tonic_status_conversion_not_found() {
    let status = tonic::Status::not_found("not found");
    let error: ApiError = status.into();

    match error {
        ApiError::NotFound(msg) => assert_eq!(msg, "not found"),
        _ => panic!("Expected NotFound error"),
    }
}

#[test]
fn test_tonic_status_conversion_invalid_argument() {
    let status = tonic::Status::invalid_argument("bad input");
    let error: ApiError = status.into();

    match error {
        ApiError::BadRequest(msg) => assert_eq!(msg, "bad input"),
        _ => panic!("Expected BadRequest error"),
    }
}

#[test]
fn test_tonic_status_conversion_permission_denied() {
    let status = tonic::Status::permission_denied("no access");
    let error: ApiError = status.into();

    match error {
        ApiError::Forbidden(msg) => assert_eq!(msg, "no access"),
        _ => panic!("Expected Forbidden error"),
    }
}

#[test]
fn test_tonic_status_conversion_unavailable() {
    let status = tonic::Status::unavailable("service down");
    let error: ApiError = status.into();

    match error {
        ApiError::EngineError(msg) => assert!(msg.contains("service down")),
        _ => panic!("Expected EngineError error"),
    }
}

#[test]
fn test_tonic_status_conversion_other() {
    let status = tonic::Status::internal("internal error");
    let error: ApiError = status.into();

    match error {
        ApiError::EngineError(msg) => assert_eq!(msg, "internal error"),
        _ => panic!("Expected EngineError error"),
    }
}
