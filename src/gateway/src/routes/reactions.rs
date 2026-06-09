use axum::extract::{Path, Query, State};
use axum::Extension;
use axum::Json;

use crate::error::ApiError;
use crate::models::auth::Claims;
use crate::models::context::EncodeTextRequest;
use crate::models::context::EncodeTextResponse;
use crate::models::reaction::*;
use crate::models::SuccessResponse;
use crate::AppState;

/// POST /api/v1/reactions
pub async fn create_reaction(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(req): Json<ProcessReactionRequest>,
) -> Result<Json<SuccessResponse<ReactionResult>>, ApiError> {
    let mut client = state.engines.resonance.as_ref().clone();
    let result = client.process_reaction(&claims.sub, req).await?;
    Ok(Json(SuccessResponse::ok(result)))
}

/// POST /api/v1/reactions/batch
pub async fn create_batch(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(req): Json<ProcessBatchRequest>,
) -> Result<Json<SuccessResponse<BatchResult>>, ApiError> {
    let mut client = state.engines.resonance.as_ref().clone();
    let result = client.process_batch(&claims.sub, req).await?;
    Ok(Json(SuccessResponse::ok(result)))
}

/// GET /api/v1/reactions?anchor_id=xxx
pub async fn list_reactions(
    State(state): State<AppState>,
    Query(params): Query<ReactionListQuery>,
) -> Result<Json<SuccessResponse<serde_json::Value>>, ApiError> {
    let anchor_id = params
        .anchor_id
        .ok_or_else(|| ApiError::BadRequest("缺少 anchor_id 参数".into()))?;

    let list_params = ReactionListParams {
        page: params.page,
        page_size: params.page_size,
        filter_type: params.filter_type,
    };

    let mut client = state.engines.resonance.as_ref().clone();
    let (reactions, total_count, has_more) = client.list_reactions(&anchor_id, list_params).await?;

    Ok(Json(SuccessResponse::ok(serde_json::json!({
        "reactions": reactions,
        "total_count": total_count,
        "has_more": has_more,
    }))))
}

/// GET /api/v1/reactions/distribution/:anchor_id
pub async fn get_distribution(
    State(state): State<AppState>,
    Path(anchor_id): Path<String>,
) -> Result<Json<SuccessResponse<ReactionDistribution>>, ApiError> {
    let mut client = state.engines.resonance.as_ref().clone();
    let dist = client.get_reaction_distribution(&anchor_id).await?;
    Ok(Json(SuccessResponse::ok(dist)))
}

/// GET /api/v1/relationships/score?user_a=xxx&user_b=xxx
pub async fn get_relationship_score(
    State(state): State<AppState>,
    Query(params): Query<RelationshipQuery>,
) -> Result<Json<SuccessResponse<RelationshipScore>>, ApiError> {
    let user_a = params
        .user_a
        .ok_or_else(|| ApiError::BadRequest("缺少 user_a 参数".into()))?;
    let user_b = params
        .user_b
        .ok_or_else(|| ApiError::BadRequest("缺少 user_b 参数".into()))?;

    let mut client = state.engines.resonance.as_ref().clone();
    let score = client.get_relationship_score(&user_a, &user_b).await?;
    Ok(Json(SuccessResponse::ok(score)))
}

/// GET /api/v1/relationships/:user_id
pub async fn find_resonance_pairs(
    State(state): State<AppState>,
    Path(user_id): Path<String>,
) -> Result<Json<SuccessResponse<Vec<ResonancePair>>>, ApiError> {
    let mut client = state.engines.resonance.as_ref().clone();
    let pairs = client.find_resonance_pairs(&user_id).await?;
    Ok(Json(SuccessResponse::ok(pairs)))
}

/// POST /api/v1/encode
pub async fn encode_text(
    State(state): State<AppState>,
    Json(req): Json<EncodeTextRequest>,
) -> Result<Json<SuccessResponse<EncodeTextResponse>>, ApiError> {
    let mut client = state.engines.resonance.as_ref().clone();
    let result = client.encode_text(req.texts).await?;
    Ok(Json(SuccessResponse::ok(result)))
}

#[derive(serde::Deserialize)]
pub struct ReactionListQuery {
    pub anchor_id: Option<String>,
    pub page: Option<u32>,
    pub page_size: Option<u32>,
    pub filter_type: Option<String>,
}

#[derive(serde::Deserialize)]
pub struct RelationshipQuery {
    pub user_a: Option<String>,
    pub user_b: Option<String>,
}
