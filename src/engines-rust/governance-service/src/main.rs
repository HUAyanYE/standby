//! Standby Governance HTTP Service
//!
//! 将治理评估算法暴露为 HTTP JSON 服务，供 Python 引擎调用。

use std::collections::HashMap;
use warp::Filter;

use standby_governance::credit::{update_marker_credit_bayesian, time_decayed_credit};
use standby_governance::evaluate::{evaluate_governance, GovernanceDecision};
use standby_governance::detection::{detect_velocity_anomaly, detect_coordinated_marking, detect_topic_type_attack};
use standby_shared::types::{ContentReaction, MarkerRecord};

// ============================================================
// 请求/响应类型
// ============================================================

#[derive(Debug, Clone, serde::Deserialize)]
pub struct EvaluateRequest {
    pub anchor_id: String,
    pub resonance: u32,
    pub neutral: u32,
    pub opposition: u32,
    pub unexperienced: u32,
    pub harmful: u32,
    pub marker_credits: Vec<f64>,
    pub base_threshold: f64,
    pub min_samples: u32,
    pub current_ts: f64,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct EvaluateResponse {
    pub level: String,
    pub harmful_weight: f64,
    pub marker_avg_credit: f64,
    pub reason: String,
    pub actions: Vec<String>,
}

#[derive(Debug, Clone, serde::Deserialize)]
pub struct DetectAnomalyRequest {
    pub timestamps: Vec<f64>,
    pub marker_ids: Vec<String>,
    pub reactions_by_type: HashMap<String, (u32, u32)>,
    pub time_window_seconds: f64,
    pub threshold: usize,
    pub unexperienced_threshold: f64,
    pub min_samples: u32,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct DetectAnomalyResponse {
    pub velocity: AnomalyResult,
    pub coordinated: AnomalyResult,
    pub type_attack: AnomalyResult,
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct AnomalyResult {
    pub detected: bool,
    pub reason: String,
}

// ============================================================
// 服务实现
// ============================================================

fn level_to_string(level: &standby_shared::types::GovernanceLevel) -> String {
    match level {
        standby_shared::types::GovernanceLevel::Normal => "L0_正常".into(),
        standby_shared::types::GovernanceLevel::Observing => "L1_观察".into(),
        standby_shared::types::GovernanceLevel::Demoted => "L2_降权".into(),
        standby_shared::types::GovernanceLevel::Suspended => "L3_暂停".into(),
        standby_shared::types::GovernanceLevel::Removed => "L4_移除".into(),
        standby_shared::types::GovernanceLevel::Conflict => "争议".into(),
    }
}

async fn handle_evaluate(body: String) -> Result<impl warp::Reply, std::convert::Infallible> {
    let request: EvaluateRequest = match serde_json::from_str(&body) {
        Ok(r) => r,
        Err(e) => {
            let resp = serde_json::json!({"error": format!("JSON 解析失败: {}", e)});
            return Ok(warp::reply::json(&resp));
        }
    };

    let reactions = ContentReaction {
        anchor_id: request.anchor_id,
        resonance: request.resonance,
        neutral: request.neutral,
        opposition: request.opposition,
        unexperienced: request.unexperienced,
        harmful: request.harmful,
    };

    let decision = evaluate_governance(
        &reactions,
        &request.marker_credits,
        request.base_threshold,
        request.min_samples,
        request.current_ts,
    );

    let response = EvaluateResponse {
        level: level_to_string(&decision.level),
        harmful_weight: decision.harmful_weight,
        marker_avg_credit: decision.marker_avg_credit,
        reason: decision.reason,
        actions: decision.actions,
    };

    Ok(warp::reply::json(&response))
}

async fn handle_detect_anomaly(body: String) -> Result<impl warp::Reply, std::convert::Infallible> {
    let request: DetectAnomalyRequest = match serde_json::from_str(&body) {
        Ok(r) => r,
        Err(e) => {
            let resp = serde_json::json!({"error": format!("JSON 解析失败: {}", e)});
            return Ok(warp::reply::json(&resp));
        }
    };

    // 速度异常检测
    let (velocity_detected, velocity_reason) = detect_velocity_anomaly(
        &request.timestamps,
        request.time_window_seconds,
        request.threshold,
    );

    // 协同攻击检测
    let (coordinated_detected, coordinated_reason) = detect_coordinated_marking(
        &request.timestamps,
        &request.marker_ids,
        request.time_window_seconds,
        request.threshold,
    );

    // 话题类型打击检测
    let (type_detected, type_reason) = detect_topic_type_attack(
        &request.reactions_by_type,
        request.unexperienced_threshold,
        request.min_samples,
    );

    let response = DetectAnomalyResponse {
        velocity: AnomalyResult { detected: velocity_detected, reason: velocity_reason },
        coordinated: AnomalyResult { detected: coordinated_detected, reason: coordinated_reason },
        type_attack: AnomalyResult { detected: type_detected, reason: type_reason },
    };

    Ok(warp::reply::json(&response))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .init();

    let port: u16 = std::env::var("PORT")
        .unwrap_or_else(|_| "8096".into())
        .parse()?;

    tracing::info!("Governance Service 启动在 0.0.0.0:{}", port);

    // GET /health
    let health = warp::get()
        .and(warp::path("health"))
        .and(warp::path::end())
        .map(|| warp::reply::json(&serde_json::json!({"status": "ok"})));

    // POST /evaluate (带请求体大小限制)
    let evaluate = warp::post()
        .and(warp::path("evaluate"))
        .and(warp::body::content_length_limit(1024 * 1024)) // 1MB
        .and(warp::body::bytes().map(|bytes: bytes::Bytes| {
            String::from_utf8_lossy(&bytes).to_string()
        }))
        .and_then(handle_evaluate);

    // POST /detect-anomaly (带请求体大小限制)
    let detect = warp::post()
        .and(warp::path("detect-anomaly"))
        .and(warp::body::content_length_limit(1024 * 1024)) // 1MB
        .and(warp::body::bytes().map(|bytes: bytes::Bytes| {
            String::from_utf8_lossy(&bytes).to_string()
        }))
        .and_then(handle_detect_anomaly);

    let (_, server) = warp::serve(health.or(evaluate).or(detect))
        .bind_with_graceful_shutdown(
            ([0, 0, 0, 0], port),
            async {
                tokio::signal::ctrl_c().await.expect("Failed to listen for Ctrl+C");
                tracing::info!("收到关闭信号，正在优雅关闭...");
            },
        );

    server.await;

    Ok(())
}
