//! 消息类型定义
//!
//! 定义加密/解密的消息格式

use serde::{Deserialize, Serialize};
use serde_big_array::BigArray;

/// 明文消息
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PlaintextMessage {
    pub sender_id: String,
    pub recipient_id: String,
    pub content: Vec<u8>,
    pub timestamp: u64,
    pub message_type: MessageType,
}

/// 消息类型
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum MessageType {
    /// 普通文本
    Text,
    /// 媒体引用 (加密后的媒体 ID)
    MediaRef,
    /// 反应 (共鸣/无感等)
    Reaction,
    /// 系统消息
    System,
}

/// 线路消息 (用于传输)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WireMessage {
    /// 发送者身份公钥
    pub sender_identity: [u8; 32],
    /// 接收者身份公钥
    pub recipient_identity: [u8; 32],
    /// 加密后的消息体
    pub encrypted_payload: Vec<u8>,
    /// 消息序号
    pub sequence_number: u64,
    /// 时间戳
    pub timestamp: u64,
}

/// 密钥包 (用于密钥交换)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct KeyBundle {
    pub identity_key: [u8; 32],
    pub signed_pre_key: [u8; 32],
    pub signed_pre_key_id: u32,
    #[serde(with = "BigArray")]
    pub signed_pre_key_signature: [u8; 64],
    pub one_time_pre_keys: Vec<OneTimePreKeyPublic>,
}

/// 公开的一次性预密钥
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OneTimePreKeyPublic {
    pub key_id: u32,
    pub public_key: [u8; 32],
}

/// 密钥包注册请求
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RegisterKeyBundleRequest {
    pub device_id: String,
    pub key_bundle: KeyBundle,
}

/// 密钥包查询响应
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GetKeyBundleResponse {
    pub found: bool,
    pub key_bundle: Option<KeyBundle>,
}
