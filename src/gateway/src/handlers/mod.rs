// 健康检查
use axum::Json;
use serde_json::json;

pub mod auth;
pub mod anchor;
pub mod reaction;
pub mod user;
pub mod context;
pub mod governance;

pub async fn health() -> Json<serde_json::Value> {
    Json(json!({
        "status": "healthy",
        "service": "standby-gateway",
        "version": "0.1.0",
        "timestamp": chrono::Utc::now().to_rfc3339(),
    }))
}
