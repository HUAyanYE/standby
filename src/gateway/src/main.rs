// ============================================================
// Standby API 网关 — main.rs
// ============================================================
//
// 架构:
//   客户端 (Flutter/Rust) → [TLS] → API 网关 → [gRPC] → 引擎
//
// 请求处理链:
//   1. TLS 终端
//   2. 设备指纹验证
//   3. JWT 认证
//   4. 请求签名验证
//   5. 速率限制
//   6. 路由到引擎
// ============================================================

mod auth;
mod config;
mod error;
mod handlers;
mod middleware;
mod proto;
mod state;

use std::sync::Arc;

use axum::{
    middleware as axum_mw,
    routing::{get, post},
    Router,
};
use tower_http::trace::TraceLayer;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use crate::{
    config::GatewayConfig,
    middleware::{auth_mw, device_mw, rate_limit_mw},
    state::AppState,
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 初始化日志
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "standby_gateway=info,tower_http=info".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    tracing::info!("Standby API 网关启动中...");

    // 加载配置
    let config = GatewayConfig::load()?;
    tracing::info!("配置加载完成: port={}", config.port);

    // 创建应用状态
    let state = Arc::new(AppState::new(config.clone()).await?);

    // 构建路由
    let app = build_router(state);

    // 启动服务
    let addr = format!("0.0.0.0:{}", config.port);
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    tracing::info!("API 网关监听在 {}", addr);

    axum::serve(listener, app).await?;

    Ok(())
}

/// 构建路由
fn build_router(state: Arc<AppState>) -> Router {
    // 公开路由 (无需认证)
    let public_routes = Router::new()
        .route("/health", get(handlers::health))
        .route("/auth/device", post(handlers::auth::device_auth))
        .route("/auth/refresh", post(handlers::auth::refresh_token));

    // 需要认证的路由
    let authenticated_routes = Router::new()
        // 锚点
        .route("/anchors", get(handlers::anchor::list_anchors))
        .route("/anchors/replay", get(handlers::anchor::get_replay_anchors))
        .route("/anchors/import", post(handlers::anchor::import_anchor))
        .route("/anchors/:id", get(handlers::anchor::get_anchor))
        .route("/anchors/:id/summary", get(handlers::anchor::get_reaction_summary))
        // 反应
        .route("/reactions", post(handlers::reaction::submit_reaction))
        .route("/anchors/:id/reactions", get(handlers::reaction::list_reactions))
        .route("/traces", get(handlers::reaction::get_resonance_traces))
        // 用户
        .route("/me", get(handlers::user::get_profile))
        .route("/relationships", get(handlers::user::list_relationships))
        .route("/confidants/intent", post(handlers::user::express_confidant_intent))
        .route("/confidants", get(handlers::user::list_confidants))
        // 情境
        .route("/context", post(handlers::context::submit_context_state))
        .route("/context/hint", get(handlers::context::get_contextual_hint))
        // 治理
        .route("/report", post(handlers::governance::report_content))
        .route("/content/:id/status", get(handlers::governance::get_content_status))
        .route("/appeal", post(handlers::governance::appeal_decision))
        // 中间件链: 设备指纹 → JWT 认证 → 速率限制
        .layer(axum_mw::from_fn_with_state(
            state.clone(),
            device_mw::verify_device,
        ))
        .layer(axum_mw::from_fn_with_state(
            state.clone(),
            auth_mw::verify_jwt,
        ))
        .layer(axum_mw::from_fn_with_state(
            state.clone(),
            rate_limit_mw::check_rate_limit,
        ));

    Router::new()
        .merge(public_routes)
        .merge(authenticated_routes)
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}
