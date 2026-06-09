use axum::extract::{Path, State};
use axum::Extension;
use axum::Json;

use crate::error::ApiError;
use crate::models::auth::Claims;
use crate::models::governance::*;
use crate::models::SuccessResponse;
use crate::AppState;

/// POST /api/v1/governance/evaluate
pub async fn evaluate_content(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    Json(req): Json<EvaluateContentRequest>,
) -> Result<Json<SuccessResponse<GovernanceDecision>>, ApiError> {
    let mut client = state.engines.governance.as_ref().clone();
    let decision = client.evaluate_content(req).await?;
    Ok(Json(SuccessResponse::ok(decision)))
}

/// POST /api/v1/governance/anomaly
pub async fn detect_anomaly(
    State(state): State<AppState>,
    Extension(_claims): Extension<Claims>,
    Json(req): Json<DetectAnomalyRequest>,
) -> Result<Json<SuccessResponse<Vec<AnomalyReport>>>, ApiError> {
    let mut client = state.engines.governance.as_ref().clone();
    let anomalies = client.detect_anomaly(req).await?;
    Ok(Json(SuccessResponse::ok(anomalies)))
}

/// GET /api/v1/governance/credibility/:marker_hash
pub async fn check_credibility(
    State(state): State<AppState>,
    Path(marker_hash): Path<String>,
) -> Result<Json<SuccessResponse<MarkerCredibility>>, ApiError> {
    let mut client = state.engines.governance.as_ref().clone();
    let credibility = client.check_credibility(&marker_hash).await?;
    Ok(Json(SuccessResponse::ok(credibility)))
}
