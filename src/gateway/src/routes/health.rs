use axum::Json;
use serde::Serialize;

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
pub async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".into(),
        version: env!("CARGO_PKG_VERSION").into(),
        engines: EngineStatus {
            anchor: true,     // TODO: 实际检查引擎连接
            resonance: true,
            governance: true,
            context: true,
        },
    })
}
