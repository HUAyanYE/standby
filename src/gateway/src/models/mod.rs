pub mod auth;
pub mod anchor;
pub mod reaction;
pub mod governance;
pub mod context;

/// 统一成功响应
#[derive(serde::Serialize)]
pub struct SuccessResponse<T: serde::Serialize> {
    pub success: bool,
    pub data: T,
}

impl<T: serde::Serialize> SuccessResponse<T> {
    pub fn ok(data: T) -> Self {
        Self {
            success: true,
            data,
        }
    }
}
