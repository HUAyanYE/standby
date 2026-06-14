use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use axum::Json;
use serde::Serialize;

/// 统一 API 错误响应
#[derive(Debug, thiserror::Error)]
pub enum ApiError {
    #[error("未认证: {0}")]
    Unauthorized(String),

    #[error("禁止访问: {0}")]
    Forbidden(String),

    #[error("资源不存在: {0}")]
    NotFound(String),

    #[error("请求参数错误: {0}")]
    BadRequest(String),

    #[error("请求过于频繁，请稍后重试")]
    RateLimited,

    #[error("引擎调用失败: {0}")]
    EngineError(String),

    #[error("内部错误: {0}")]
    Internal(String),
}

#[derive(Serialize)]
struct ErrorResponse {
    error: ErrorDetail,
}

#[derive(Serialize)]
struct ErrorDetail {
    code: String,
    message: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    request_id: Option<String>,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let (status, code) = match &self {
            ApiError::Unauthorized(_) => (StatusCode::UNAUTHORIZED, "UNAUTHORIZED"),
            ApiError::Forbidden(_) => (StatusCode::FORBIDDEN, "FORBIDDEN"),
            ApiError::NotFound(_) => (StatusCode::NOT_FOUND, "NOT_FOUND"),
            ApiError::BadRequest(_) => (StatusCode::BAD_REQUEST, "BAD_REQUEST"),
            ApiError::RateLimited => (StatusCode::TOO_MANY_REQUESTS, "RATE_LIMITED"),
            ApiError::EngineError(_) => (StatusCode::BAD_GATEWAY, "ENGINE_ERROR"),
            ApiError::Internal(_) => (StatusCode::INTERNAL_SERVER_ERROR, "INTERNAL_ERROR"),
        };

        let body = ErrorResponse {
            error: ErrorDetail {
                code: code.to_string(),
                message: self.to_string(),
                request_id: None, // 将由中间件注入
            },
        };

        (status, Json(body)).into_response()
    }
}

impl From<tonic::Status> for ApiError {
    fn from(status: tonic::Status) -> Self {
        match status.code() {
            tonic::Code::NotFound => ApiError::NotFound(status.message().to_string()),
            tonic::Code::InvalidArgument => ApiError::BadRequest(status.message().to_string()),
            tonic::Code::PermissionDenied => ApiError::Forbidden(status.message().to_string()),
            tonic::Code::Unavailable => {
                ApiError::EngineError(format!("引擎不可用: {}", status.message()))
            }
            _ => ApiError::EngineError(status.message().to_string()),
        }
    }
}
