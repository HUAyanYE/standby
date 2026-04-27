// 错误处理
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;

/// 网关错误类型
#[derive(Debug, thiserror::Error)]
pub enum GatewayError {
    #[error("认证失败: {0}")]
    AuthError(String),
    
    #[error("设备验证失败: {0}")]
    DeviceError(String),
    
    #[error("速率限制")]
    RateLimited,
    
    #[error("引擎调用失败: {0}")]
    EngineError(String),
    
    #[error("内部错误: {0}")]
    Internal(#[from] anyhow::Error),
}

impl IntoResponse for GatewayError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            GatewayError::AuthError(msg) => (StatusCode::UNAUTHORIZED, msg),
            GatewayError::DeviceError(msg) => (StatusCode::BAD_REQUEST, msg),
            GatewayError::RateLimited => (
                StatusCode::TOO_MANY_REQUESTS,
                "请求过于频繁，请稍后再试".to_string(),
            ),
            GatewayError::EngineError(msg) => (StatusCode::BAD_GATEWAY, msg),
            GatewayError::Internal(e) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                format!("服务器内部错误: {}", e),
            ),
        };
        
        let body = json!({
            "error": true,
            "message": message,
            "code": status.as_u16(),
        });
        
        (status, Json(body)).into_response()
    }
}
