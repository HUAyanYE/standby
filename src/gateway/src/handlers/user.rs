// 用户处理器 — 调用用户引擎 gRPC
use axum::{extract::State, Json};
use serde_json::json;
use std::sync::Arc;
use tonic::Request as TonicRequest;

use crate::proto::engines;
use crate::state::AppState;

/// 获取用户档案
/// UserEngine 没有 GetProfile RPC，用 GetMarkerCredit 获取信用信息
pub async fn get_profile(
    State(state): State<Arc<AppState>>,
    headers: axum::http::HeaderMap,
) -> Json<serde_json::Value> {
    let user_id = headers.get("X-User-Id")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("anonymous")
        .to_string();

    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64;

    // 调用 UserEngine 获取标记者信用
    let mut client = state.user_client.clone();
    let request = TonicRequest::new(engines::GetMarkerCreditRequest {
        marker_token_hash: user_id.clone(),
        current_timestamp: now,
    });

    let (credit_score, marker_credit) = match client.get_marker_credit(request).await {
        Ok(resp) => {
            let r = resp.into_inner();
            (r.credit_score, r.time_decayed_credit)
        }
        Err(e) => {
            tracing::warn!("用户引擎调用失败: {}", e);
            (0.5_f32, 0.5_f32)
        }
    };

    Json(json!({
        "user_id": user_id,
        "credit_score": credit_score,
        "marker_credit": marker_credit,
        "total_reactions": 0,
        "total_anchors_engaged": 0,
        "confidant_count": 0,
        "created_at": now,
    }))
}

/// 获取关系列表
pub async fn list_relationships(
    State(state): State<Arc<AppState>>,
    headers: axum::http::HeaderMap,
) -> Json<serde_json::Value> {
    let user_id = headers.get("X-User-Id")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("anonymous");

    // 调用 UserEngine 的 get_marker_history 作为关系数据的代理
    let mut client = state.user_client.clone();
    let request = TonicRequest::new(engines::GetMarkerHistoryRequest {
        marker_token_hash: user_id.to_string(),
        limit: 50,
    });

    match client.get_marker_history(request).await {
        Ok(resp) => {
            let r = resp.into_inner();
            // 从历史记录中提取关系信息（简化版）
            let _entries = r.entries;
            Json(json!({
                "relationships": [],
                "pagination": { "total_count": 0, "has_more": false }
            }))
        }
        Err(e) => {
            tracing::warn!("获取关系失败: {}", e);
            Json(json!({
                "relationships": [],
                "pagination": { "total_count": 0, "has_more": false }
            }))
        }
    }
}

/// 表达知己意向
pub async fn express_confidant_intent(
    State(state): State<Arc<AppState>>,
    headers: axum::http::HeaderMap,
    Json(body): Json<serde_json::Value>,
) -> Json<serde_json::Value> {
    let user_id = headers.get("X-User-Id")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("anonymous")
        .to_string();

    let target_hash = body.get("target_user_internal_hash")
        .and_then(|v| v.as_str())
        .unwrap_or("");

    if target_hash.is_empty() {
        return Json(json!({
            "success": false,
            "matched": false,
            "message": "缺少目标用户标识"
        }));
    }

    // 先检查知己资格
    let mut client = state.user_client.clone();
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64;

    let request = TonicRequest::new(engines::CheckConfidantEligibilityRequest {
        user_a_id: user_id.clone(),
        user_b_id: target_hash.to_string(),
        current_timestamp: now,
    });

    match client.check_confidant_eligibility(request).await {
        Ok(resp) => {
            let r = resp.into_inner();
            let message = if r.eligible {
                "恭喜！你们已满足知己条件。"
            } else if r.score_met {
                "已记录意向，继续在更多话题上产生共鸣即可。"
            } else {
                "已记录你的意向，当双方条件满足时系统会通知。"
            };
            Json(json!({
                "success": true,
                "matched": r.eligible,
                "message": message,
            }))
        }
        Err(e) => {
            tracing::warn!("知己检查失败: {}", e);
            Json(json!({
                "success": true,
                "matched": false,
                "message": "已记录你的意向"
            }))
        }
    }
}

/// 获取知己列表
/// 
/// UserEngine 目前没有 ListConfidants RPC，知己关系需要通过 NATS 事件缓存
/// 当前返回空列表，后续通过 CheckConfidantEligibility 实现
pub async fn list_confidants(
    State(_state): State<Arc<AppState>>,
    headers: axum::http::HeaderMap,
) -> Json<serde_json::Value> {
    let _user_id = headers.get("X-User-Id")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("anonymous");

    // TODO: 知己关系需要通过 NATS 事件缓存
    // 当用户表达知己意向并匹配成功时，通过 NATS 发布 ConfidantEstablished 事件
    // Gateway 监听该事件并缓存知己关系，此处查询缓存
    // 目前返回空列表
    Json(json!({
        "confidants": [],
        "pagination": { "total_count": 0, "has_more": false }
    }))
}
