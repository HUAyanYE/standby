// 治理处理器 (用户侧) — 调用治理引擎 gRPC
use axum::{extract::Path, extract::State, Json};
use serde::Deserialize;
use serde_json::json;
use std::sync::Arc;
use tonic::Request as TonicRequest;

use crate::proto::engines;
use crate::state::AppState;

#[derive(Deserialize)]
pub struct ReportBody {
    pub content_id: String,
    pub content_type: String,
    pub report_type: String,
    pub reason: String,
}

#[derive(Deserialize)]
pub struct AppealBody {
    pub decision_id: String,
    pub appeal_reason: String,
}

/// 举报内容 — 调用治理引擎 DetectAnomaly 评估
pub async fn report_content(
    State(state): State<Arc<AppState>>,
    Json(body): Json<ReportBody>,
) -> Json<serde_json::Value> {
    if body.reason.trim().is_empty() {
        return Json(json!({"accepted": false, "message": "请填写举报理由"}));
    }

    tracing::info!("举报: content={}, type={}, reason={}", body.content_id, body.report_type, body.reason);

    // 调用治理引擎检测异常
    let mut client = state.governance_client.clone();
    let request = TonicRequest::new(engines::DetectAnomalyRequest {
        anchor_id: body.content_id.clone(),
        mark_timestamps: vec![chrono::Utc::now().timestamp() as f32],
        marker_ids: vec!["reporter".to_string()],
        reactions_by_type: std::collections::HashMap::new(),
    });

    match client.detect_anomaly(request).await {
        Ok(resp) => {
            let r = resp.into_inner();
            if r.anomaly_detected {
                let types: Vec<String> = r.anomalies.iter()
                    .map(|a| a.anomaly_type.clone())
                    .collect();
                tracing::info!("举报触发异常检测: {:?}", types);
            }
            Json(json!({
                "accepted": true,
                "message": "已收到举报，系统将进行评估"
            }))
        }
        Err(e) => {
            tracing::warn!("治理引擎调用失败: {}", e);
            Json(json!({
                "accepted": true,
                "message": "已收到举报，将在 24 小时内处理"
            }))
        }
    }
}

/// 获取内容治理状态 — 调用治理引擎 EvaluateContent
pub async fn get_content_status(
    State(state): State<Arc<AppState>>,
    Path(content_id): Path<String>,
) -> Json<serde_json::Value> {
    let mut client = state.governance_client.clone();

    // 构造一个空的 reaction_summary 来查询当前状态
    use crate::proto::common;
    let request = TonicRequest::new(engines::EvaluateContentRequest {
        content_id: content_id.clone(),
        content_type: common::ContentSource::Anchor as i32,
        text: String::new(),
        vector: vec![],
        reaction_summary: Some(common::ReactionSummary {
            anchor_id: content_id.clone(),
            resonance_count: 0,
            neutral_count: 0,
            opposition_count: 0,
            unexperienced_count: 0,
            harmful_count: 0,
            total_count: 0,
            updated_at: 0,
        }),
        marker_credits: vec![],
    });

    match client.evaluate_content(request).await {
        Ok(resp) => {
            let r = resp.into_inner();
            if let Some(decision) = r.decision {
                let level_name = match decision.level {
                    1 => "L0_正常",
                    2 => "L1_观察",
                    3 => "L2_降权",
                    4 => "L3_暂停",
                    5 => "L4_移除",
                    6 => "争议",
                    _ => "L0_正常",
                };
                let can_appeal = decision.level >= 3; // L2 以上可申诉
                Json(json!({
                    "level": level_name,
                    "status_message": decision.reason,
                    "can_appeal": can_appeal,
                    "harmful_weight": decision.harmful_weight,
                }))
            } else {
                Json(json!({
                    "level": "L0_正常",
                    "status_message": "内容状态正常",
                    "can_appeal": false,
                }))
            }
        }
        Err(e) => {
            tracing::warn!("治理引擎调用失败: {}", e);
            Json(json!({
                "level": "L0_正常",
                "status_message": "内容状态正常",
                "can_appeal": false,
            }))
        }
    }
}

/// 申诉治理决策
pub async fn appeal_decision(
    State(state): State<Arc<AppState>>,
    Json(body): Json<AppealBody>,
) -> Json<serde_json::Value> {
    if body.appeal_reason.trim().is_empty() {
        return Json(json!({"accepted": false, "message": "请填写申诉理由"}));
    }

    tracing::info!("申诉: decision={}, reason={}", body.decision_id, body.appeal_reason);

    // TODO: 申诉需要持久化到数据库，目前记录日志
    // 后续接入 PostgreSQL 的 appeals 表
    let mut client = state.governance_client.clone();

    // 更新标记者信用（申诉成功=准确标记）
    let request = TonicRequest::new(engines::UpdateMarkerCreditRequest {
        updates: vec![engines::MarkerCreditUpdate {
            marker_token_hash: body.decision_id.clone(),
            was_accurate: false, // 申诉 = 原标记可能不准确
            timestamp: chrono::Utc::now().timestamp(),
        }],
    });

    match client.update_marker_credit(request).await {
        Ok(_) => {
            tracing::info!("申诉已记录，标记者信用已更新");
        }
        Err(e) => {
            tracing::warn!("信用更新失败: {}", e);
        }
    }

    Json(json!({
        "accepted": true,
        "message": "申诉已提交，将在 24 小时内处理"
    }))
}
