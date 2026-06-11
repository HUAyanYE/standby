//! Standby E2EE 加密层
//!
//! 实现 Signal 协议的核心组件:
//! - X3DH (Extended Triple Diffie-Hellman): 密钥协商
//! - Double Ratchet: 消息加密/解密
//! - HKDF: 密钥派生
//! - ChaCha20-Poly1305: 对称加密
//!
//! 设计原则:
//! - 所有密钥操作在端侧完成
//! - 服务端只存储加密后的密文和公钥
//! - 前向保密: 每条消息使用独立密钥

pub mod error;
pub mod keys;
pub mod x3dh;
pub mod ratchet;
pub mod message;
pub mod session;

pub use error::CryptoError;
pub use keys::{IdentityKey, SignedPreKey, OneTimePreKey, EphemeralKey};
pub use x3dh::{X3DHResult, x3dh_initiate, x3dh_respond, PreKeyBundle};
pub use ratchet::{DoubleRatchet, EncryptedMessage};
pub use message::{PlaintextMessage, WireMessage, KeyBundle};
pub use session::{Session, SessionManager};
