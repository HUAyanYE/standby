use axum::extract::State;
use axum::Extension;
use axum::Json;
use chrono::Utc;
use jsonwebtoken::{encode, EncodingKey, Header};
use sha2::{Digest, Sha256};

use crate::error::ApiError;
use crate::models::auth::*;
use crate::models::SuccessResponse;
use crate::AppState;

/// POST /api/v1/auth/register
///
/// 设备指纹注册:
/// 1. 验证设备指纹非空
/// 2. 计算设备指纹哈希 (SHA-256)
/// 3. 查询是否已注册 (基于 internal_token)
/// 4. 若未注册 → 写入 users 表
/// 5. 签发 JWT
pub async fn register(
    State(state): State<AppState>,
    Json(req): Json<RegisterRequest>,
) -> Result<Json<SuccessResponse<AuthResponse>>, ApiError> {
    if req.device_fingerprint.is_empty() {
        return Err(ApiError::BadRequest("device_fingerprint 不能为空".into()));
    }

    let device_hash = hash_device_fingerprint(&req.device_fingerprint);
    let internal_token = format!("token_{}", &device_hash[..32]);

    // 查询是否已注册
    let existing = sqlx::query_scalar::<_, uuid::Uuid>(
        "SELECT id FROM users WHERE internal_token = $1"
    )
    .bind(&internal_token)
    .fetch_optional(&state.db)
    .await
    .map_err(|e| ApiError::Internal(format!("数据库查询失败: {}", e)))?;

    let user_id = if let Some(id) = existing {
        // 已注册，返回现有 ID
        id.to_string()
    } else {
        // 新注册，写入数据库
        let new_id = uuid::Uuid::new_v4();
        sqlx::query(
            r#"
            INSERT INTO users (id, internal_token, device_fingerprint, marker_credit, trust_level)
            VALUES ($1, $2, $3, 0.5, 1)
            "#
        )
        .bind(new_id)
        .bind(&internal_token)
        .bind(&device_hash)
        .execute(&state.db)
        .await
        .map_err(|e| ApiError::Internal(format!("用户注册失败: {}", e)))?;

        tracing::info!(user_id = %new_id, "新用户注册");
        new_id.to_string()
    };

    // 签发 JWT
    let token = issue_jwt(&state, &user_id, &device_hash)?;

    Ok(Json(SuccessResponse::ok(token)))
}

/// POST /api/v1/auth/login
///
/// 设备指纹登录:
/// 1. 验证设备指纹非空
/// 2. 计算设备指纹哈希
/// 3. 查询 users 表
/// 4. 若存在 → 签发 JWT
/// 5. 若不存在 → 返回 401
pub async fn login(
    State(state): State<AppState>,
    Json(req): Json<LoginRequest>,
) -> Result<Json<SuccessResponse<AuthResponse>>, ApiError> {
    if req.device_fingerprint.is_empty() {
        return Err(ApiError::BadRequest("device_fingerprint 不能为空".into()));
    }

    let device_hash = hash_device_fingerprint(&req.device_fingerprint);
    let internal_token = format!("token_{}", &device_hash[..32]);

    // 查询用户
    let user = sqlx::query_as::<_, UserRow>(
        "SELECT id, internal_token, device_fingerprint, marker_credit, trust_level, created_at FROM users WHERE internal_token = $1"
    )
    .bind(&internal_token)
    .fetch_optional(&state.db)
    .await
    .map_err(|e| ApiError::Internal(format!("数据库查询失败: {}", e)))?;

    match user {
        Some(u) => {
            // 验证设备指纹是否匹配
            if u.device_fingerprint != device_hash {
                return Err(ApiError::Unauthorized("设备指纹不匹配".into()));
            }

            let token = issue_jwt(&state, &u.id.to_string(), &device_hash)?;
            Ok(Json(SuccessResponse::ok(token)))
        }
        None => Err(ApiError::Unauthorized("设备未注册，请先注册".into())),
    }
}

/// POST /api/v1/auth/refresh
///
/// 刷新 JWT (需要当前有效 token)
pub async fn refresh(
    State(state): State<AppState>,
    Extension(claims): Extension<Claims>,
) -> Result<Json<SuccessResponse<AuthResponse>>, ApiError> {
    let token = issue_jwt(&state, &claims.sub, &claims.device_id)?;
    Ok(Json(SuccessResponse::ok(token)))
}

/// 签发 JWT
fn issue_jwt(state: &AppState, user_id: &str, device_id: &str) -> Result<AuthResponse, ApiError> {
    let now = Utc::now().timestamp() as u64;
    let expires_at = now + state.config.jwt_expiry_hours * 3600;

    let claims = Claims {
        sub: user_id.to_string(),
        device_id: device_id.to_string(),
        iat: now,
        exp: expires_at,
    };

    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(state.config.jwt_secret.as_bytes()),
    )
    .map_err(|e| ApiError::Internal(format!("JWT 签发失败: {}", e)))?;

    Ok(AuthResponse {
        token,
        user_id: user_id.to_string(),
        expires_at,
    })
}

/// 设备指纹哈希 (SHA-256)
fn hash_device_fingerprint(fingerprint: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(fingerprint.as_bytes());
    let result = hasher.finalize();
    hex::encode(result)
}

/// 数据库用户行
#[derive(Debug, sqlx::FromRow)]
#[allow(dead_code)]
struct UserRow {
    id: uuid::Uuid,
    internal_token: String,
    device_fingerprint: String,
    marker_credit: f32,
    trust_level: i16,
    created_at: chrono::NaiveDateTime,
}
