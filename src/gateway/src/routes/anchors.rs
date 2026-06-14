use axum::extract::{Path, Query, State};
use axum::Extension;
use axum::Json;

use crate::error::ApiError;
use crate::models::anchor::*;
use crate::models::auth::Claims;
use crate::models::SuccessResponse;
use crate::AppState;

/// POST /api/v1/anchors
pub async fn create_anchor(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    Json(req): Json<GenerateAnchorRequest>,
) -> Result<Json<SuccessResponse<serde_json::Value>>, ApiError> {
    req.validate().map_err(ApiError::BadRequest)?;
    let mut client = state.engines.anchor.as_ref().clone();
    let (anchor_id, quality_score) = client.generate_anchor(req).await?;

    Ok(Json(SuccessResponse::ok(serde_json::json!({
        "anchor_id": anchor_id,
        "quality_score": quality_score,
    }))))
}

/// GET /api/v1/anchors
pub async fn list_anchors(
    State(state): State<AppState>,
    Query(params): Query<PaginationParams>,
) -> Result<Json<SuccessResponse<serde_json::Value>>, ApiError> {
    let mut client = state.engines.anchor.as_ref().clone();
    let (anchors, total_count, has_more) = client.list_anchors(params).await?;

    Ok(Json(SuccessResponse::ok(serde_json::json!({
        "anchors": anchors,
        "total_count": total_count,
        "has_more": has_more,
    }))))
}

/// GET /api/v1/anchors/:id
pub async fn get_anchor(
    State(state): State<AppState>,
    Path(anchor_id): Path<String>,
) -> Result<Json<SuccessResponse<AnchorDetail>>, ApiError> {
    let mut client = state.engines.anchor.as_ref().clone();
    let anchor = client.get_anchor_metadata(&anchor_id).await?;
    Ok(Json(SuccessResponse::ok(anchor)))
}

/// GET /api/v1/anchors/:id/memory
pub async fn get_group_memory(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Path(anchor_id): Path<String>,
) -> Result<Json<SuccessResponse<GroupMemory>>, ApiError> {
    let mut client = state.engines.anchor.as_ref().clone();
    let memory = client.get_group_memory(&anchor_id, &claims.sub).await?;
    Ok(Json(SuccessResponse::ok(memory)))
}

/// GET /api/v1/anchors/:id/chain
pub async fn get_feeling_chain(
    State(state): State<AppState>,
    Path(anchor_id): Path<String>,
    Query(params): Query<FeelingChainParams>,
) -> Result<Json<SuccessResponse<Vec<FeelingChainNode>>>, ApiError> {
    let max_depth = params.validated_max_depth();
    let mut client = state.engines.anchor.as_ref().clone();
    let nodes = client.get_feeling_chain(&anchor_id, max_depth).await?;
    Ok(Json(SuccessResponse::ok(nodes)))
}
