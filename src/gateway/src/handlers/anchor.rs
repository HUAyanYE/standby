// 锚点处理器 — 调用锚点引擎 gRPC
use axum::{
    extract::{Path, Query, State},
    Json,
};
use serde::Deserialize;
use serde_json::json;
use std::sync::Arc;

use crate::state::AppState;

#[derive(Deserialize)]
pub struct ListAnchorsQuery {
    pub page: Option<u32>,
    pub page_size: Option<u32>,
    pub topic: Option<String>,
}

/// 获取锚点列表
pub async fn list_anchors(
    State(state): State<Arc<AppState>>,
    Query(query): Query<ListAnchorsQuery>,
) -> Json<serde_json::Value> {
    let mut client = state.anchor_client.clone();
    let request = tonic::Request::new(crate::proto::engines::ListAnchorsRequest {
        page: query.page.unwrap_or(1) as i32,
        page_size: query.page_size.unwrap_or(20) as i32,
        topic_filter: query.topic.unwrap_or_default(),
    });
    match client.list_anchors(request).await {
        Ok(response) => {
            let resp = response.into_inner();
            let anchors: Vec<serde_json::Value> = resp.anchors.iter().map(|a| {
                json!({
                    "anchor_id": a.anchor_id,
                    "text": a.text,
                    "topics": a.topics,
                    "quality_score": a.quality_score,
                    "reaction_count": a.reaction_count,
                    "created_at": a.created_at,
                })
            }).collect();
            Json(json!({
                "anchors": anchors,
                "pagination": { "total_count": resp.total_count, "has_more": resp.has_more }
            }))
        }
        Err(e) => {
            tracing::error!("锚点列表查询失败: {}", e);
            Json(json!({
                "anchors": [],
                "pagination": { "total_count": 0, "has_more": false }
            }))
        }
    }
}

/// 获取单个锚点详情
pub async fn get_anchor(
    State(state): State<Arc<AppState>>,
    Path(anchor_id): Path<String>,
) -> Json<serde_json::Value> {
    let mut client = state.anchor_client.clone();
    let request = tonic::Request::new(crate::proto::engines::GetAnchorMetadataRequest {
        anchor_id: anchor_id.clone(),
    });
    match client.get_anchor_metadata(request).await {
        Ok(response) => {
            let resp = response.into_inner();
            if resp.found {
                Json(json!({
                    "found": true,
                    "anchor": {
                        "anchor_id": resp.anchor_id,
                        "text": "",
                        "anchor_type": format!("{:?}", resp.anchor_type()),
                        "topics": resp.topics,
                        "source_attribution": "",
                        "quality_score": resp.quality_score,
                        "created_at": resp.created_at,
                    }
                }))
            } else {
                Json(json!({"found": false}))
            }
        }
        Err(e) => {
            tracing::error!("锚点引擎调用失败: {}", e);
            Json(json!({"found": false}))
        }
    }
}

/// 获取重现锚点 — 调用 Anchor Engine 的 ListAnchors
pub async fn get_replay_anchors(
    State(state): State<Arc<AppState>>,
    Query(query): Query<ListAnchorsQuery>,
) -> Json<serde_json::Value> {
    let mut client = state.anchor_client.clone();
    let request = tonic::Request::new(crate::proto::engines::ListAnchorsRequest {
        page: query.page.unwrap_or(1) as i32,
        page_size: query.page_size.unwrap_or(20) as i32,
        topic_filter: query.topic.unwrap_or_default(),
    });
    match client.list_anchors(request).await {
        Ok(response) => {
            let resp = response.into_inner();
            let anchors: Vec<serde_json::Value> = resp.anchors.iter().map(|a| {
                json!({
                    "anchor_id": a.anchor_id,
                    "text": a.text,
                    "topics": a.topics,
                    "quality_score": a.quality_score,
                    "reaction_count": a.reaction_count,
                    "created_at": a.created_at,
                })
            }).collect();
            Json(json!({
                "anchors": anchors,
                "pagination": {
                    "total_count": resp.total_count,
                    "has_more": resp.has_more,
                }
            }))
        }
        Err(e) => {
            tracing::error!("获取重现锚点失败: {}", e);
            Json(json!({
                "anchors": [],
                "pagination": {"total_count": 0, "has_more": false}
            }))
        }
    }
}

/// 导入锚点素材 — 调用 GenerateAnchor 实际注册
pub async fn import_anchor(
    State(state): State<Arc<AppState>>,
    Json(body): Json<serde_json::Value>,
) -> Json<serde_json::Value> {
    let content = body.get("content_text").and_then(|v| v.as_str()).unwrap_or("");
    if content.len() < 10 {
        return Json(json!({"accepted": false, "message": "内容过短 (需至少100字)"}));
    }
    let topics: Vec<String> = body.get("topics")
        .and_then(|v| v.as_array())
        .map(|arr| arr.iter().filter_map(|v| v.as_str().map(String::from)).collect())
        .unwrap_or_default();

    let mut client = state.anchor_client.clone();
    let request = tonic::Request::new(crate::proto::engines::GenerateAnchorRequest {
        source_texts: vec![content.to_string()],
        source_type: "user_content".to_string(),
        topic_hints: topics,
        user_reactions: vec![],
    });
    match client.generate_anchor(request).await {
        Ok(response) => {
            let resp = response.into_inner();
            if resp.success {
                let anchor = resp.anchor.unwrap_or_default();
                Json(json!({
                    "accepted": true,
                    "anchor_id": anchor.anchor_id,
                    "quality_score": resp.quality_score,
                    "message": "锚点已注册"
                }))
            } else {
                Json(json!({"accepted": false, "message": resp.rejection_reason}))
            }
        }
        Err(e) => {
            tracing::error!("锚点注册失败: {}", e);
            Json(json!({"accepted": false, "message": "注册服务暂时不可用"}))
        }
    }
}

/// 获取反应统计
pub async fn get_reaction_summary(
    State(state): State<Arc<AppState>>,
    Path(anchor_id): Path<String>,
) -> Json<serde_json::Value> {
    let mut client = state.resonance_client.clone();
    let request = tonic::Request::new(crate::proto::engines::GetReactionDistributionRequest {
        anchor_id: anchor_id.clone(),
    });
    match client.get_reaction_distribution(request).await {
        Ok(response) => {
            let resp = response.into_inner();
            if resp.found {
                if let Some(dist) = resp.distribution {
                    return Json(json!({
                        "found": true,
                        "summary": {
                            "anchor_id": anchor_id,
                            "resonance_count": dist.resonance_count,
                            "neutral_count": dist.neutral_count,
                            "opposition_count": dist.opposition_count,
                            "unexperienced_count": dist.unexperienced_count,
                            "harmful_count": dist.harmful_count,
                            "total_count": dist.total_count,
                        }
                    }));
                }
            }
            Json(json!({"found": false}))
        }
        Err(_) => Json(json!({"found": false})),
    }
}
