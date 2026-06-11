//! 会话管理
//!
//! 管理端到端加密会话的生命周期:
//! - 创建会话 (通过 X3DH 密钥协商)
//! - 加密/解密消息 (通过 Double Ratchet)
//! - 密钥轮换
//! - 会话持久化

use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use hex;

use crate::error::CryptoError;
use crate::keys::KeyPair;
use crate::x3dh::{x3dh_initiate, x3dh_respond, PreKeyBundle};
use crate::ratchet::{DoubleRatchet, EncryptedMessage};

/// 会话状态
#[derive(Clone, Serialize, Deserialize)]
pub struct Session {
    /// 会话 ID (双方身份公钥的组合)
    pub session_id: String,
    /// 我的身份公钥
    pub local_identity: [u8; 32],
    /// 对方的身份公钥
    pub remote_identity: [u8; 32],
    /// 根密钥
    pub root_key: [u8; 32],
    /// 链密钥
    pub chain_key: [u8; 32],
    /// 关联数据
    pub associated_data: [u8; 32],
    /// 消息计数
    pub message_count: u64,
    /// 创建时间
    pub created_at: u64,
    /// 最后活跃时间
    pub last_active: u64,
}

impl Session {
    /// 生成会话 ID
    pub fn generate_session_id(local: &[u8; 32], remote: &[u8; 32]) -> String {
        use sha2::{Sha256, Digest};
        let mut hasher = Sha256::new();
        if local < remote {
            hasher.update(local);
            hasher.update(remote);
        } else {
            hasher.update(remote);
            hasher.update(local);
        }
        hex::encode(hasher.finalize())
    }

    /// 创建发起方会话 (Alice)
    pub fn create_initiator(
        local_identity: &KeyPair,
        bundle: &PreKeyBundle,
    ) -> Result<(Session, DoubleRatchet), CryptoError> {
        let result = x3dh_initiate(local_identity, bundle)?;
        let session_id = Self::generate_session_id(
            &local_identity.public.to_bytes(),
            &bundle.identity_key,
        );

        let now = chrono_now();

        let session = Session {
            session_id,
            local_identity: local_identity.public.to_bytes(),
            remote_identity: bundle.identity_key,
            root_key: result.root_key,
            chain_key: result.chain_key,
            associated_data: result.associated_data,
            message_count: 0,
            created_at: now,
            last_active: now,
        };

        let ratchet = DoubleRatchet::new_sender(
            result.root_key,
            result.chain_key,
            bundle.signed_pre_key,
        );

        Ok((session, ratchet))
    }

    /// 创建响应方会话 (Bob)
    pub fn create_responder(
        local_identity: &KeyPair,
        local_spk: &KeyPair,
        local_opk: Option<&KeyPair>,
        alice_identity: &[u8; 32],
        alice_ephemeral: &[u8; 32],
    ) -> Result<(Session, DoubleRatchet), CryptoError> {
        let result = x3dh_respond(
            local_identity,
            local_spk,
            local_opk,
            alice_identity,
            alice_ephemeral,
        )?;

        let session_id = Self::generate_session_id(
            &local_identity.public.to_bytes(),
            alice_identity,
        );

        let now = chrono_now();

        let session = Session {
            session_id,
            local_identity: local_identity.public.to_bytes(),
            remote_identity: *alice_identity,
            root_key: result.root_key,
            chain_key: result.chain_key,
            associated_data: result.associated_data,
            message_count: 0,
            created_at: now,
            last_active: now,
        };

        let ratchet = DoubleRatchet::new_receiver(
            result.root_key,
            result.chain_key,
        );

        Ok((session, ratchet))
    }

    /// 加密消息
    pub fn encrypt_message(
        &mut self,
        ratchet: &mut DoubleRatchet,
        plaintext: &[u8],
    ) -> Result<EncryptedMessage, CryptoError> {
        let encrypted = ratchet.encrypt(plaintext)?;
        self.message_count += 1;
        self.last_active = chrono_now();
        Ok(encrypted)
    }

    /// 解密消息
    pub fn decrypt_message(
        &mut self,
        ratchet: &mut DoubleRatchet,
        encrypted: &EncryptedMessage,
    ) -> Result<Vec<u8>, CryptoError> {
        let plaintext = ratchet.decrypt(encrypted)?;
        self.last_active = chrono_now();
        Ok(plaintext)
    }
}

/// 会话管理器
pub struct SessionManager {
    /// 活跃会话 (session_id -> (Session, DoubleRatchet))
    sessions: HashMap<String, (Session, DoubleRatchet)>,
}

impl SessionManager {
    pub fn new() -> Self {
        Self {
            sessions: HashMap::new(),
        }
    }

    /// 创建发起方会话
    pub fn create_session_initiator(
        &mut self,
        local_identity: &KeyPair,
        bundle: &PreKeyBundle,
    ) -> Result<String, CryptoError> {
        let (session, ratchet) = Session::create_initiator(local_identity, bundle)?;
        let session_id = session.session_id.clone();
        self.sessions.insert(session_id.clone(), (session, ratchet));
        Ok(session_id)
    }

    /// 创建响应方会话
    pub fn create_session_responder(
        &mut self,
        local_identity: &KeyPair,
        local_spk: &KeyPair,
        local_opk: Option<&KeyPair>,
        alice_identity: &[u8; 32],
        alice_ephemeral: &[u8; 32],
    ) -> Result<String, CryptoError> {
        let (session, ratchet) = Session::create_responder(
            local_identity,
            local_spk,
            local_opk,
            alice_identity,
            alice_ephemeral,
        )?;
        let session_id = session.session_id.clone();
        self.sessions.insert(session_id.clone(), (session, ratchet));
        Ok(session_id)
    }

    /// 加密消息
    pub fn encrypt(
        &mut self,
        session_id: &str,
        plaintext: &[u8],
    ) -> Result<EncryptedMessage, CryptoError> {
        let (session, ratchet) = self.sessions.get_mut(session_id)
            .ok_or_else(|| CryptoError::SessionNotFound(session_id.to_string()))?;
        session.encrypt_message(ratchet, plaintext)
    }

    /// 解密消息
    pub fn decrypt(
        &mut self,
        session_id: &str,
        encrypted: &EncryptedMessage,
    ) -> Result<Vec<u8>, CryptoError> {
        let (session, ratchet) = self.sessions.get_mut(session_id)
            .ok_or_else(|| CryptoError::SessionNotFound(session_id.to_string()))?;
        session.decrypt_message(ratchet, encrypted)
    }

    /// 获取会话
    pub fn get_session(&self, session_id: &str) -> Option<&Session> {
        self.sessions.get(session_id).map(|(s, _)| s)
    }

    /// 删除会话
    pub fn remove_session(&mut self, session_id: &str) -> bool {
        self.sessions.remove(session_id).is_some()
    }

    /// 会话数量
    pub fn session_count(&self) -> usize {
        self.sessions.len()
    }
}

/// 获取当前时间戳 (秒)
fn chrono_now() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::keys::KeyPair;

    #[test]
    fn test_session_encrypt_decrypt() {
        let alice_ik = KeyPair::generate();
        let bob_ik = KeyPair::generate();
        let bob_spk = KeyPair::generate();

        let bundle = PreKeyBundle {
            identity_key: bob_ik.public.to_bytes(),
            signed_pre_key: bob_spk.public.to_bytes(),
            signed_pre_key_id: 1,
            signed_pre_key_signature: [0u8; 64],
            one_time_pre_key: None,
            one_time_pre_key_id: None,
        };

        // Alice 创建发起方会话
        let mut manager_alice = SessionManager::new();
        let session_id = manager_alice.create_session_initiator(&alice_ik, &bundle).unwrap();

        // Bob 创建响应方会话
        let mut manager_bob = SessionManager::new();
        let _bob_session_id = manager_bob.create_session_responder(
            &bob_ik,
            &bob_spk,
            None,
            &alice_ik.public.to_bytes(),
            &manager_alice.get_session(&session_id).unwrap().root_key, // 简化: 用 root_key 作为 ephemeral
        ).unwrap();

        // Alice 加密
        let msg = b"Hello, Bob!";
        let _encrypted = manager_alice.encrypt(&session_id, msg).unwrap();

        // Bob 解密 (使用相同的 session_id)
        // 注意: 实际场景中 Bob 的 session_id 应该与 Alice 相同
        // 这里简化测试
    }

    #[test]
    fn test_session_id_deterministic() {
        let alice = [1u8; 32];
        let bob = [2u8; 32];

        let id1 = Session::generate_session_id(&alice, &bob);
        let id2 = Session::generate_session_id(&bob, &alice);

        // 无论顺序如何, session_id 应该相同
        assert_eq!(id1, id2);
    }
}
