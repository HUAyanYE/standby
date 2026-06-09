use axum::extract::{Request, State};
use axum::http::header;
use axum::middleware::Next;
use axum::response::Response;
use jsonwebtoken::{decode, DecodingKey, Validation, Algorithm};

use crate::error::ApiError;
use crate::models::auth::Claims;
use crate::AppState;

/// JWT 验证中间件
///
/// 从 Authorization: Bearer <token> 提取并验证 JWT
/// 验证通过后将 Claims 注入请求扩展
pub async fn jwt_auth(
    State(state): State<AppState>,
    mut request: Request,
    next: Next,
) -> Result<Response, ApiError> {
    // 白名单路由跳过 JWT 验证
    let path = request.uri().path();
    if is_jwt_exempt(path) {
        return Ok(next.run(request).await);
    }

    let auth_header = request
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|v| v.to_str().ok())
        .ok_or_else(|| ApiError::Unauthorized("缺少 Authorization 头".into()))?;

    let token = auth_header
        .strip_prefix("Bearer ")
        .ok_or_else(|| ApiError::Unauthorized("Authorization 头格式错误，需要 Bearer token".into()))?;

    let mut validation = Validation::new(Algorithm::HS256);
    validation.set_required_spec_claims(&["sub", "exp"]);

    let token_data = decode::<Claims>(
        token,
        &DecodingKey::from_secret(state.config.jwt_secret.as_bytes()),
        &validation,
    )
    .map_err(|e| ApiError::Unauthorized(format!("JWT 验证失败: {}", e)))?;

    // 将 Claims 注入请求扩展
    request.extensions_mut().insert(token_data.claims);

    Ok(next.run(request).await)
}

/// JWT 白名单路由
fn is_jwt_exempt(path: &str) -> bool {
    matches!(
        path,
        "/health"
            | "/api/v1/auth/register"
            | "/api/v1/auth/login"
    )
}
