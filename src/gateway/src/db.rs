//! 数据库连接池

use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;

use crate::config::GatewayConfig;

/// 创建 PostgreSQL 连接池
pub async fn create_pool(_config: &GatewayConfig) -> anyhow::Result<PgPool> {
    let database_url = std::env::var("DATABASE_URL").unwrap_or_else(|_| {
        let password = std::env::var("POSTGRES_PASSWORD")
            .expect("POSTGRES_PASSWORD 环境变量必须设置");
        format!(
            "postgres://{}:{}@{}:{}/{}",
            std::env::var("POSTGRES_USER").unwrap_or_else(|_| "standby".into()),
            password,
            std::env::var("POSTGRES_HOST").unwrap_or_else(|_| "localhost".into()),
            std::env::var("POSTGRES_PORT").unwrap_or_else(|_| "5432".into()),
            std::env::var("POSTGRES_DB").unwrap_or_else(|_| "standby".into()),
        )
    });

    let pool = PgPoolOptions::new()
        .max_connections(10)
        .connect(&database_url)
        .await?;

    tracing::info!("PostgreSQL 连接池已创建");
    Ok(pool)
}
