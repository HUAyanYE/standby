use axum::extract::State;
use axum::Json;
use serde::Serialize;

use crate::AppState;

#[derive(Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
    pub engines: EngineStatus,
}

#[derive(Serialize)]
pub struct EngineStatus {
    pub anchor: bool,
    pub resonance: bool,
    pub governance: bool,
    pub context: bool,
}

/// GET /health
pub async fn health_check(State(state): State<AppState>) -> Json<HealthResponse> {
    let engines = state.engines.clone();

    let timeout = std::time::Duration::from_secs(3);

    let (anchor, resonance, governance, context) = tokio::join!(
        async { tokio::time::timeout(timeout, engines.anchor.check_health()).await.unwrap_or(false) },
        async { tokio::time::timeout(timeout, engines.resonance.check_health()).await.unwrap_or(false) },
        async { tokio::time::timeout(timeout, engines.governance.check_health()).await.unwrap_or(false) },
        async { tokio::time::timeout(timeout, engines.context.check_health()).await.unwrap_or(false) },
    );

    let all_ok = anchor && resonance && governance && context;

    Json(HealthResponse {
        status: if all_ok { "ok" } else { "degraded" }.into(),
        version: env!("CARGO_PKG_VERSION").into(),
        engines: EngineStatus {
            anchor,
            resonance,
            governance,
            context,
        },
    })
}
