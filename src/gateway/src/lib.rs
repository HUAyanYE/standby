//! Standby API Gateway Library
//!
//! 导出模块供测试使用

pub mod config;
pub mod error;
pub mod middleware;
pub mod models;

pub mod db;
pub mod engine_clients;
mod proto;
pub mod routes;

use std::sync::Arc;
use config::GatewayConfig;

/// 应用状态 — 注入到所有 handler
#[derive(Clone)]
pub struct AppState {
    pub config: Arc<GatewayConfig>,
    pub engines: engine_clients::EngineClients,
    pub db: sqlx::PgPool,
}
