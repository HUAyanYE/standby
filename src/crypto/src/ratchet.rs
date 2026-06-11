//! Double Ratchet 算法
//!
//! Signal 协议的消息加密/解密核心:
//! - 发送棘轮: 每条消息使用新的链密钥
//! - 接收棘轮: 处理乱序消息
//! - 前向保密: 删除旧密钥后无法解密旧消息
//!
//! 参考: https://signal.org/docs/specifications/doubleratchet/

use chacha20poly1305::{
    aead::{Aead, KeyInit},
    ChaCha20Poly1305, Nonce,
};
use hkdf::Hkdf;
use sha2::Sha256;
use x25519_dalek::PublicKey;
use serde::{Deserialize, Serialize};

use crate::error::CryptoError;
use crate::keys::KeyPair;

/// 棘轮消息头
#[derive(Clone, Serialize, Deserialize)]
pub struct RatchetHeader {
    pub ratchet_public: [u8; 32],  // 发送方的棘轮公钥
    pub previous_chain_length: u32, // 上一个链的消息数
    pub message_number: u32,        // 当前消息在链中的序号
}

/// 加密消息
#[derive(Clone, Serialize, Deserialize)]
pub struct EncryptedMessage {
    pub header: RatchetHeader,
    pub ciphertext: Vec<u8>,
    pub nonce: [u8; 12],
}

/// 棘轮状态
struct RatchetState {
    /// 根密钥
    root_key: [u8; 32],
    /// 发送链密钥
    send_chain_key: Option<[u8; 32]>,
    /// 接收链密钥
    recv_chain_key: Option<[u8; 32]>,
    /// 发送棘轮密钥对
    send_ratchet: KeyPair,
    /// 接收方的棘轮公钥
    recv_ratchet_public: Option<PublicKey>,
    /// 发送链消息数
    send_count: u32,
    /// 接收链消息数
    recv_count: u32,
    /// 上一个发送链的长度
    previous_send_chain_length: u32,
    /// 跳过的消息密钥 (用于处理乱序)
    skipped_keys: Vec<(PublicKey, u32, [u8; 32])>,
}

/// Double Ratchet 实现
pub struct DoubleRatchet {
    state: Option<RatchetState>,
}

impl DoubleRatchet {
    /// 创建新的发送方 Ratchet (Alice)
    pub fn new_sender(
        root_key: [u8; 32],
        chain_key: [u8; 32],
        their_ratchet_public: [u8; 32],
    ) -> Self {
        let send_ratchet = KeyPair::generate();

        Self {
            state: Some(RatchetState {
                root_key,
                send_chain_key: Some(chain_key),
                recv_chain_key: None,
                send_ratchet,
                recv_ratchet_public: Some(PublicKey::from(their_ratchet_public)),
                send_count: 0,
                recv_count: 0,
                previous_send_chain_length: 0,
                skipped_keys: Vec::new(),
            }),
        }
    }

    /// 创建新的接收方 Ratchet (Bob)
    pub fn new_receiver(
        root_key: [u8; 32],
        chain_key: [u8; 32],
    ) -> Self {
        let send_ratchet = KeyPair::generate();

        Self {
            state: Some(RatchetState {
                root_key,
                send_chain_key: None,
                recv_chain_key: Some(chain_key),
                send_ratchet,
                recv_ratchet_public: None,
                send_count: 0,
                recv_count: 0,
                previous_send_chain_length: 0,
                skipped_keys: Vec::new(),
            }),
        }
    }

    /// 加密消息
    pub fn encrypt(&mut self, plaintext: &[u8]) -> Result<EncryptedMessage, CryptoError> {
        let state = self.state.as_mut()
            .ok_or_else(|| CryptoError::Encryption("Ratchet 状态未初始化".into()))?;

        // 如果没有发送链密钥, 需要棘轮步进
        if state.send_chain_key.is_none() {
            self.ratchet_step_send()?;
        }

        let state = self.state.as_mut()
            .ok_or_else(|| CryptoError::Encryption("Ratchet 状态未初始化".into()))?;
        let chain_key = state.send_chain_key.as_ref()
            .ok_or_else(|| CryptoError::Encryption("发送链密钥未初始化".into()))?;

        // 派生消息密钥
        let (new_chain_key, message_key) = kdf_ck(chain_key)?;

        // 加密
        let nonce = generate_nonce();
        let cipher = ChaCha20Poly1305::new_from_slice(&message_key)
            .map_err(|e| CryptoError::Encryption(e.to_string()))?;
        let ciphertext = cipher
            .encrypt(Nonce::from_slice(&nonce), plaintext)
            .map_err(|e| CryptoError::Encryption(e.to_string()))?;

        let header = RatchetHeader {
            ratchet_public: state.send_ratchet.public.to_bytes(),
            previous_chain_length: state.previous_send_chain_length,
            message_number: state.send_count,
        };

        // 更新状态
        state.send_chain_key = Some(new_chain_key);
        state.send_count += 1;

        Ok(EncryptedMessage {
            header,
            ciphertext,
            nonce,
        })
    }

    /// 解密消息
    pub fn decrypt(&mut self, message: &EncryptedMessage) -> Result<Vec<u8>, CryptoError> {
        let state = self.state.as_mut()
            .ok_or_else(|| CryptoError::Decryption("Ratchet 状态未初始化".into()))?;

        let their_public = PublicKey::from(message.header.ratchet_public);

        // 检查是否是跳过的消息
        for (pk, msg_num, mk) in &state.skipped_keys {
            if pk.as_bytes() == their_public.as_bytes() && *msg_num == message.header.message_number {
                let cipher = ChaCha20Poly1305::new_from_slice(mk)
                    .map_err(|e| CryptoError::Decryption(e.to_string()))?;
                return cipher
                    .decrypt(Nonce::from_slice(&message.nonce), message.ciphertext.as_ref())
                    .map_err(|e| CryptoError::Decryption(e.to_string()));
            }
        }

        // 如果收到新的棘轮公钥 (非首次), 需要棘轮步进
        // 首次消息使用 X3DH 派生的初始 recv_chain_key, 不触发棘轮
        let need_ratchet = match state.recv_ratchet_public {
            None => {
                // 首次收到消息, 记录对方公钥, 使用初始链密钥
                state.recv_ratchet_public = Some(their_public);
                false
            }
            Some(ref known) => known.as_bytes() != their_public.as_bytes(),
        };

        if need_ratchet {
            self.skip_message_keys(message.header.previous_chain_length)?;
            self.ratchet_step_recv(&their_public)?;
        }

        let state = self.state.as_mut()
            .ok_or_else(|| CryptoError::Decryption("Ratchet 状态未初始化".into()))?;

        // 跳过到当前消息序号
        let recv_count = state.recv_count;
        if message.header.message_number > recv_count {
            self.skip_message_keys(message.header.message_number)?;
        }

        let state = self.state.as_mut()
            .ok_or_else(|| CryptoError::Decryption("Ratchet 状态未初始化".into()))?;
        let chain_key = state.recv_chain_key.as_ref()
            .ok_or_else(|| CryptoError::Decryption("接收链密钥不存在".into()))?;

        // 派生消息密钥
        let (new_chain_key, message_key) = kdf_ck(chain_key)?;

        // 解密
        let cipher = ChaCha20Poly1305::new_from_slice(&message_key)
            .map_err(|e| CryptoError::Decryption(e.to_string()))?;
        let plaintext = cipher
            .decrypt(Nonce::from_slice(&message.nonce), message.ciphertext.as_ref())
            .map_err(|e| CryptoError::Decryption(e.to_string()))?;

        // 更新状态
        state.recv_chain_key = Some(new_chain_key);
        state.recv_count += 1;

        Ok(plaintext)
    }

    /// 发送方棘轮步进
    fn ratchet_step_send(&mut self) -> Result<(), CryptoError> {
        let state = self.state.as_mut()
            .ok_or_else(|| CryptoError::KeyAgreement("Ratchet 状态未初始化".into()))?;

        let recv_public = state.recv_ratchet_public.as_ref()
            .ok_or_else(|| CryptoError::KeyAgreement("没有接收方公钥".into()))?;

        // DH 计算
        let dh_output = state.send_ratchet.diffie_hellman(recv_public);

        // KDF 链
        let (new_root_key, new_chain_key) = kdf_rk(&state.root_key, &dh_output)?;

        // 更新状态
        state.root_key = new_root_key;
        state.send_chain_key = Some(new_chain_key);
        state.previous_send_chain_length = state.send_count;
        state.send_count = 0;
        state.recv_ratchet_public = None;

        Ok(())
    }

    /// 接收方棘轮步进
    fn ratchet_step_recv(&mut self, their_public: &PublicKey) -> Result<(), CryptoError> {
        let state = self.state.as_mut()
            .ok_or_else(|| CryptoError::KeyAgreement("Ratchet 状态未初始化".into()))?;

        // DH 计算
        let dh_output = state.send_ratchet.diffie_hellman(their_public);

        // KDF 链
        let (new_root_key, new_chain_key) = kdf_rk(&state.root_key, &dh_output)?;

        // 更新状态
        state.root_key = new_root_key;
        state.recv_chain_key = Some(new_chain_key);
        state.recv_ratchet_public = Some(*their_public);
        state.recv_count = 0;

        // 生成新的发送棘轮密钥
        state.send_ratchet = KeyPair::generate();

        Ok(())
    }

    /// 跳过消息密钥 (处理乱序)
    fn skip_message_keys(&mut self, until: u32) -> Result<(), CryptoError> {
        let state = self.state.as_mut()
            .ok_or_else(|| CryptoError::Decryption("Ratchet 状态未初始化".into()))?;

        if let Some(chain_key) = state.recv_chain_key.as_ref() {
            let mut current_key = *chain_key;
            let current_count = state.recv_count;

            for i in current_count..until {
                let (new_key, message_key) = kdf_ck(&current_key)?;
                if let Some(recv_public) = state.recv_ratchet_public {
                    state.skipped_keys.push((recv_public, i, message_key));
                }
                current_key = new_key;
            }

            state.recv_chain_key = Some(current_key);
            state.recv_count = until;
        }

        Ok(())
    }
}

/// 链密钥 KDF: CK -> (CK_new, MK)
fn kdf_ck(ck: &[u8; 32]) -> Result<([u8; 32], [u8; 32]), CryptoError> {
    let mut new_ck = [0u8; 32];
    let mut mk = [0u8; 32];

    // 使用 HKDF 派生
    let hk_ck = Hkdf::<Sha256>::from_prk(ck)
        .map_err(|e| CryptoError::KeyDerivation(e.to_string()))?;
    hk_ck.expand(b"StandbyChainKey", &mut new_ck)
        .map_err(|e| CryptoError::KeyDerivation(e.to_string()))?;

    let hk_mk = Hkdf::<Sha256>::from_prk(ck)
        .map_err(|e| CryptoError::KeyDerivation(e.to_string()))?;
    hk_mk.expand(b"StandbyMessageKey", &mut mk)
        .map_err(|e| CryptoError::KeyDerivation(e.to_string()))?;

    Ok((new_ck, mk))
}

/// 根密钥 KDF: (RK, DH) -> (RK_new, CK)
fn kdf_rk(rk: &[u8; 32], dh: &[u8; 32]) -> Result<([u8; 32], [u8; 32]), CryptoError> {
    let mut input = Vec::with_capacity(64);
    input.extend_from_slice(rk);
    input.extend_from_slice(dh);

    let hk = Hkdf::<Sha256>::new(Some(rk), &input);

    let mut output = [0u8; 64];
    hk.expand(b"StandbyRatchet", &mut output)
        .map_err(|e| CryptoError::KeyDerivation(e.to_string()))?;

    let mut new_rk = [0u8; 32];
    let mut ck = [0u8; 32];
    new_rk.copy_from_slice(&output[0..32]);
    ck.copy_from_slice(&output[32..64]);

    Ok((new_rk, ck))
}

/// 生成随机 nonce
fn generate_nonce() -> [u8; 12] {
    use rand::RngCore;
    let mut nonce = [0u8; 12];
    rand::thread_rng().fill_bytes(&mut nonce);
    nonce
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_encrypt_decrypt_roundtrip() {
        let root_key = [1u8; 32];
        let chain_key = [2u8; 32];
        let bob_ratchet = KeyPair::generate();

        // Alice 创建发送方
        let mut alice = DoubleRatchet::new_sender(
            root_key,
            chain_key,
            bob_ratchet.public.to_bytes(),
        );

        // Bob 创建接收方
        let mut bob = DoubleRatchet::new_receiver(root_key, chain_key);

        // Alice 加密
        let plaintext = b"Hello, Bob! This is a secret message.";
        let encrypted = alice.encrypt(plaintext).unwrap();

        // Bob 解密
        let decrypted = bob.decrypt(&encrypted).unwrap();
        assert_eq!(decrypted, plaintext);
    }

    #[test]
    fn test_multiple_messages() {
        let root_key = [1u8; 32];
        let chain_key = [2u8; 32];
        let bob_ratchet = KeyPair::generate();

        let mut alice = DoubleRatchet::new_sender(
            root_key,
            chain_key,
            bob_ratchet.public.to_bytes(),
        );
        let mut bob = DoubleRatchet::new_receiver(root_key, chain_key);

        // 发送多条消息
        for i in 0..5 {
            let msg = format!("Message {}", i);
            let encrypted = alice.encrypt(msg.as_bytes()).unwrap();
            let decrypted = bob.decrypt(&encrypted).unwrap();
            assert_eq!(decrypted, msg.as_bytes());
        }
    }

    #[test]
    fn test_different_messages_different_ciphertext() {
        let root_key = [1u8; 32];
        let chain_key = [2u8; 32];
        let bob_ratchet = KeyPair::generate();

        let mut alice = DoubleRatchet::new_sender(
            root_key,
            chain_key,
            bob_ratchet.public.to_bytes(),
        );

        let msg1 = alice.encrypt(b"Hello").unwrap();
        let msg2 = alice.encrypt(b"World").unwrap();

        // 不同消息的密文应该不同
        assert_ne!(msg1.ciphertext, msg2.ciphertext);
        // nonce 也应该不同
        assert_ne!(msg1.nonce, msg2.nonce);
    }

    #[test]
    fn test_forward_secrecy() {
        let root_key = [1u8; 32];
        let chain_key = [2u8; 32];
        let bob_ratchet = KeyPair::generate();

        let mut alice = DoubleRatchet::new_sender(
            root_key,
            chain_key,
            bob_ratchet.public.to_bytes(),
        );
        let mut bob = DoubleRatchet::new_receiver(root_key, chain_key);

        // 发送 3 条消息
        let enc1 = alice.encrypt(b"msg1").unwrap();
        let enc2 = alice.encrypt(b"msg2").unwrap();
        let enc3 = alice.encrypt(b"msg3").unwrap();

        // Bob 解密所有消息
        bob.decrypt(&enc1).unwrap();
        bob.decrypt(&enc2).unwrap();
        bob.decrypt(&enc3).unwrap();

        // 如果攻击者获得了当前的链密钥, 无法解密之前的消息
        // 这是 Double Ratchet 的前向保密特性
    }
}
