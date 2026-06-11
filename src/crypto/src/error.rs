//! 加密层错误类型

use thiserror::Error;

#[derive(Error, Debug)]
pub enum CryptoError {
    #[error("密钥生成失败: {0}")]
    KeyGeneration(String),

    #[error("密钥协商失败: {0}")]
    KeyAgreement(String),

    #[error("加密失败: {0}")]
    Encryption(String),

    #[error("解密失败: {0}")]
    Decryption(String),

    #[error("密钥派生失败: {0}")]
    KeyDerivation(String),

    #[error("无效的密钥格式: {0}")]
    InvalidKey(String),

    #[error("消息格式错误: {0}")]
    MessageFormat(String),

    #[error("会话不存在: {0}")]
    SessionNotFound(String),

    #[error("序列化失败: {0}")]
    Serialization(#[from] serde_json::Error),
}
