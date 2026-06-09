use axum::extract::{Query, State};
use axum::Extension;
use axum::Json;

use crate::error::ApiError;
use crate::models::auth::Claims;
use crate::models::context::*;
use crate::models::SuccessResponse;
use crate::AppState;

/// POST /api/v1/context
pub async fn submit_context(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Json(req): Json<SubmitContextRequest>,
) -> Result<Json<SuccessResponse<serde_json::Value>>, ApiError> {
    let mut client = state.engines.context.as_ref().clone();
    let accepted = client.submit_context(&claims.sub, req).await?;
    Ok(Json(SuccessResponse::ok(serde_json::json!({
        "accepted": accepted,
    }))))
}

/// GET /api/v1/context/weights?topics=孤独,城市,时间
pub async fn get_weights(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
    Query(params): Query<ContextualWeightsParams>,
) -> Result<Json<SuccessResponse<ContextualWeights>>, ApiError> {
    let topics: Vec<String> = params
        .topics
        .split(',')
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .collect();

    let mut client = state.engines.context.as_ref().clone();
    let weights = client.get_contextual_weights(&claims.sub, topics).await?;
    Ok(Json(SuccessResponse::ok(weights)))
}
