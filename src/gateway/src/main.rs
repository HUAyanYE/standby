//! Standby API Gateway
//!
//! REST-to-gRPC 代理，提供:
//! - JWT + 设备指纹认证
//! - 速率限制
//! - 请求日志
//! - 引擎代理转发

mod config;
mod db;
mod engine_clients;
mod error;
mod middleware;
mod models;
mod proto;
mod routes;

use std::sync::Arc;
use std::time::Duration;

use axum::http::header;
use axum::middleware::from_fn_with_state;
use axum::Router;
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;
use tracing_subscriber::EnvFilter;

use config::GatewayConfig;
use engine_clients::EngineClients;
use middleware::{device_auth, jwt, rate_limit, request_log};

/// 应用状态 — 注入到所有 handler
#[derive(Clone)]
pub struct AppState {
    pub config: Arc<GatewayConfig>,
    pub engines: EngineClients,
    pub db: sqlx::PgPool,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 加载配置
    let config = GatewayConfig::from_env()?;

    // 初始化日志
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| EnvFilter::new(&config.log_level)),
        )
        .json()
        .init();

    tracing::info!("启动 Standby API Gateway");
    tracing::info!("端口: {}", config.port);

    // 连接引擎
    let engines = EngineClients::new(
        &config.engine_anchor_url,
        &config.engine_resonance_url,
        &config.engine_governance_url,
        &config.engine_context_url,
    )
    .await?;

    tracing::info!("引擎连接已建立");

    // 连接数据库
    let db_pool = db::create_pool(&config).await?;

    // 速率限制器
    let rate_limiter = Arc::new(rate_limit::RateLimiter::new(config.rate_limit_per_minute));

    // 启动限流器定期清理任务 (每 5 分钟清理过期条目)
    let cleanup_limiter = rate_limiter.clone();
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(Duration::from_secs(300));
        loop {
            interval.tick().await;
            cleanup_limiter.cleanup();
            tracing::debug!("限流器过期条目已清理");
        }
    });

    // 应用状态
    let state = AppState {
        config: Arc::new(config.clone()),
        engines,
        db: db_pool,
    };

    // CORS — 从环境变量读取允许的域名
    let allowed_origins: Vec<axum::http::HeaderValue> = std::env::var("CORS_ALLOWED_ORIGINS")
        .unwrap_or_else(|_| "http://localhost:3000,http://localhost:8080".into())
        .split(',')
        .filter_map(|s| s.trim().parse().ok())
        .collect();

    let cors = CorsLayer::new()
        .allow_origin(allowed_origins)
        .allow_methods([
            axum::http::Method::GET,
            axum::http::Method::POST,
            axum::http::Method::OPTIONS,
        ])
        .allow_headers(vec![
            header::AUTHORIZATION,
            header::CONTENT_TYPE,
            "x-device-id".parse().unwrap(),
            "x-device-signature".parse().unwrap(),
            "x-request-timestamp".parse().unwrap(),
        ]);

    // 构建路由
    let app = Router::new()
        // 健康检查 (无中间件)
        .route("/health", axum::routing::get(routes::health::health_check))
        // 认证路由 (无 JWT，有设备认证)
        .route("/api/v1/auth/register", axum::routing::post(routes::auth::register))
        .route("/api/v1/auth/login", axum::routing::post(routes::auth::login))
        .route("/api/v1/auth/refresh", axum::routing::post(routes::auth::refresh))
        // 锚点路由
        .route("/api/v1/anchors", axum::routing::get(routes::anchors::list_anchors))
        .route("/api/v1/anchors", axum::routing::post(routes::anchors::create_anchor))
        .route("/api/v1/anchors/:id", axum::routing::get(routes::anchors::get_anchor))
        .route("/api/v1/anchors/:id/memory", axum::routing::get(routes::anchors::get_group_memory))
        .route("/api/v1/anchors/:id/chain", axum::routing::get(routes::anchors::get_feeling_chain))
        // 反应路由
        .route("/api/v1/reactions", axum::routing::get(routes::reactions::list_reactions))
        .route("/api/v1/reactions", axum::routing::post(routes::reactions::create_reaction))
        .route("/api/v1/reactions/batch", axum::routing::post(routes::reactions::create_batch))
        .route("/api/v1/reactions/distribution/:anchor_id", axum::routing::get(routes::reactions::get_distribution))
        // 关系路由
        .route("/api/v1/relationships/score", axum::routing::get(routes::reactions::get_relationship_score))
        .route("/api/v1/relationships/:user_id", axum::routing::get(routes::reactions::find_resonance_pairs))
        // 治理路由
        .route("/api/v1/governance/evaluate", axum::routing::post(routes::governance::evaluate_content))
        .route("/api/v1/governance/anomaly", axum::routing::post(routes::governance::detect_anomaly))
        .route("/api/v1/governance/credibility/:marker_hash", axum::routing::get(routes::governance::check_credibility))
        // 情境路由
        .route("/api/v1/context", axum::routing::post(routes::context::submit_context))
        .route("/api/v1/context/weights", axum::routing::get(routes::context::get_weights))
        // 编码路由
        .route("/api/v1/encode", axum::routing::post(routes::reactions::encode_text))
        // 中间件 — Axum .layer() 最后添加的最先执行
        // 执行顺序: request_log → rate_limit → jwt_auth → device_auth → handler
        .layer(from_fn_with_state(state.clone(), request_log::request_log))
        .layer(cors)
        .layer(TraceLayer::new_for_http())
        .layer(from_fn_with_state(rate_limiter, rate_limit::rate_limit))
        // 设备认证 (需要在 JWT 之后，因为依赖 Claims)
        .layer(from_fn_with_state(state.clone(), device_auth::device_auth))
        // JWT 验证 (先于设备认证执行)
        .layer(from_fn_with_state(state.clone(), jwt::jwt_auth))
        .with_state(state);

    // 启动服务
    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{}", config.port)).await?;
    tracing::info!("Gateway 监听在 0.0.0.0:{}", config.port);

    axum::serve(listener, app).await?;

    Ok(())
}
