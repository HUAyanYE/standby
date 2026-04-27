// 情境处理器 — 调用情境引擎 gRPC
use axum::{extract::State, Json};
use serde::Deserialize;
use serde_json::json;
use std::sync::Arc;
use tonic::Request as TonicRequest;

use crate::proto::engines;
use crate::state::AppState;

#[derive(Deserialize)]
pub struct ContextStateBody {
    pub scene_type: String,
    pub mood_hint: String,
    pub attention_level: String,
    pub active_device: String,
}

/// 提交情境状态 → 调用 ContextEngine gRPC
pub async fn submit_context_state(
    State(state): State<Arc<AppState>>,
    headers: axum::http::HeaderMap,
    Json(body): Json<ContextStateBody>,
) -> Json<serde_json::Value> {
    let user_id = headers.get("X-User-Id")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("anonymous")
        .to_string();

    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64;

    tracing::info!(
        "情境状态: user={}, scene={}, mood={}, attention={}",
        user_id, body.scene_type, body.mood_hint, body.attention_level
    );

    let mut client = state.context_client.clone();
    let request = TonicRequest::new(engines::ContextStateRequest {
        user_id,
        scene_type: body.scene_type,
        mood_hint: body.mood_hint,
        attention_level: body.attention_level,
        active_device: crate::proto::common::DeviceType::Phone as i32,
        timestamp: now,
    });

    match client.submit_context_state(request).await {
        Ok(resp) => {
            Json(json!({"accepted": resp.into_inner().accepted}))
        }
        Err(e) => {
            tracing::warn!("情境引擎调用失败: {}", e);
            // 降级: 仍然接受，不影响核心流程
            Json(json!({"accepted": true}))
        }
    }
}

/// 获取情境化提示 → 调用 ContextEngine gRPC
pub async fn get_contextual_hint(
    State(state): State<Arc<AppState>>,
    headers: axum::http::HeaderMap,
) -> Json<serde_json::Value> {
    let user_id = headers.get("X-User-Id")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("anonymous")
        .to_string();

    let mut client = state.context_client.clone();
    let request = TonicRequest::new(engines::ContextualWeightsRequest {
        user_id,
        candidate_topics: vec![],
    });

    match client.get_contextual_weights(request).await {
        Ok(resp) => {
            let r = resp.into_inner();
            // 从 topic_weights 提取推荐话题
            let topics: Vec<String> = r.topic_weights.keys()
                .take(5)
                .cloned()
                .collect();
            Json(json!({
                "recommended_scene": r.recommended_scene,
                "mood_suggestion": "",
                "topic_hints": topics,
            }))
        }
        Err(e) => {
            tracing::warn!("情境引擎调用失败: {}", e);
            // 降级: 基于时间推荐
            use chrono::Timelike;
            let hour = chrono::Utc::now().hour();
            let (scene, mood, topics) = match hour {
                6..=11 => ("早晨", "平静", vec!["新开始", "希望", "日常"]),
                12..=14 => ("午间", "轻松", vec!["午餐", "放松", "小憩"]),
                15..=17 => ("下午", "专注", vec!["工作", "思考", "灵感"]),
                18..=21 => ("晚间", "反思", vec!["一天回顾", "感悟", "温暖"]),
                _ => ("深夜", "沉思", vec!["孤独", "自我", "时间", "意义"]),
            };
            Json(json!({
                "recommended_scene": scene,
                "mood_suggestion": format!("你似乎处于{}状态", mood),
                "topic_hints": topics,
            }))
        }
    }
}
