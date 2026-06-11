//! X3DH (Extended Triple Diffie-Hellman) 密钥协商
//!
//! Signal 协议的密钥协商阶段:
//! 1. Alice (发起方) 从 Bob 的预密钥包中获取公钥
//! 2. Alice 计算 4 个 DH 共享密钥
//! 3. Alice 派生初始根密钥和链密钥
//! 4. Alice 发送初始消息给 Bob
//! 5. Bob 用相同的 DH 计算恢复相同的密钥
//!
//! 参考: https://signal.org/docs/specifications/x3dh/

use hkdf::Hkdf;
use sha2::Sha256;
use x25519_dalek::PublicKey;
use serde::{Deserialize, Serialize};
use serde_big_array::BigArray;

use crate::error::CryptoError;
use crate::keys::KeyPair;

/// X3DH 协商结果
#[derive(Clone, Serialize, Deserialize)]
pub struct X3DHResult {
    /// 根密钥 (用于 Double Ratchet 初始化)
    pub root_key: [u8; 32],
    /// 链密钥 (用于第一条消息加密)
    pub chain_key: [u8; 32],
    /// 关联数据 (用于 AEAD)
    pub associated_data: [u8; 32],
    /// 发送方的临时公钥 (需要包含在初始消息中)
    pub ephemeral_public: [u8; 32],
}

/// 发起方 (Alice) 的预密钥包
#[derive(Clone, Serialize, Deserialize)]
pub struct PreKeyBundle {
    pub identity_key: [u8; 32],        // Bob 的身份公钥
    pub signed_pre_key: [u8; 32],      // Bob 的签名预公钥
    pub signed_pre_key_id: u32,
    #[serde(with = "BigArray")]
    pub signed_pre_key_signature: [u8; 64],
    pub one_time_pre_key: Option<[u8; 32]>,  // Bob 的一次性预公钥 (可选)
    pub one_time_pre_key_id: Option<u32>,
}

/// X3DH 发起方 (Alice) 计算
///
/// 输入:
/// - Alice 的身份密钥
/// - Bob 的预密钥包
///
/// 输出:
/// - X3DHResult (根密钥 + 链密钥 + 关联数据)
pub fn x3dh_initiate(
    alice_identity: &KeyPair,
    bob_bundle: &PreKeyBundle,
) -> Result<X3DHResult, CryptoError> {
    let bob_identity = PublicKey::from(bob_bundle.identity_key);
    let bob_spk = PublicKey::from(bob_bundle.signed_pre_key);

    // 生成临时密钥
    let alice_ek = KeyPair::generate();

    // 计算 4 个 DH 共享密钥
    // DH1 = DH(Alice_IK, Bob_SPK)
    let dh1 = alice_identity.diffie_hellman(&bob_spk);

    // DH2 = DH(Alice_EK, Bob_IK)
    let dh2 = alice_ek.diffie_hellman(&bob_identity);

    // DH3 = DH(Alice_EK, Bob_SPK)
    let dh3 = alice_ek.diffie_hellman(&bob_spk);

    // DH4 = DH(Alice_EK, Bob_OPK) (如果有)
    let dh4 = if let Some(opk_bytes) = bob_bundle.one_time_pre_key {
        let bob_opk = PublicKey::from(opk_bytes);
        alice_ek.diffie_hellman(&bob_opk)
    } else {
        [0u8; 32] // 无 OPK 时用零填充
    };

    // 派生根密钥和链密钥
    let (root_key, chain_key, associated_data) = derive_keys(&dh1, &dh2, &dh3, &dh4)?;

    Ok(X3DHResult {
        root_key,
        chain_key,
        associated_data,
        ephemeral_public: alice_ek.public.to_bytes(),
    })
}

/// X3DH 响应方 (Bob) 计算
///
/// 输入:
/// - Bob 的身份密钥
/// - Bob 的签名预密钥
/// - Bob 的一次性预密钥 (如果有)
/// - Alice 的身份公钥
/// - Alice 的临时公钥
///
/// 输出:
/// - X3DHResult (与 Alice 计算的相同)
pub fn x3dh_respond(
    bob_identity: &KeyPair,
    bob_spk: &KeyPair,
    bob_opk: Option<&KeyPair>,
    alice_identity_public: &[u8; 32],
    alice_ephemeral_public: &[u8; 32],
) -> Result<X3DHResult, CryptoError> {
    let alice_ik = PublicKey::from(*alice_identity_public);
    let alice_ek = PublicKey::from(*alice_ephemeral_public);

    // 计算 4 个 DH 共享密钥 (与 Alice 对称)
    // DH1 = DH(Bob_SPK, Alice_IK) = DH(Alice_IK, Bob_SPK)
    let dh1 = bob_spk.diffie_hellman(&alice_ik);

    // DH2 = DH(Bob_IK, Alice_EK) = DH(Alice_EK, Bob_IK)
    let dh2 = bob_identity.diffie_hellman(&alice_ek);

    // DH3 = DH(Bob_SPK, Alice_EK) = DH(Alice_EK, Bob_SPK)
    let dh3 = bob_spk.diffie_hellman(&alice_ek);

    // DH4 = DH(Bob_OPK, Alice_EK) = DH(Alice_EK, Bob_OPK)
    let dh4 = if let Some(opk) = bob_opk {
        opk.diffie_hellman(&alice_ek)
    } else {
        [0u8; 32]
    };

    // 派生相同的密钥
    let (root_key, chain_key, associated_data) = derive_keys(&dh1, &dh2, &dh3, &dh4)?;

    Ok(X3DHResult {
        root_key,
        chain_key,
        associated_data,
        ephemeral_public: *alice_ephemeral_public,
    })
}

/// 从 DH 共享密钥派生根密钥、链密钥和关联数据
///
/// 使用 HKDF-SHA256:
/// - IKM = DH1 || DH2 || DH3 || DH4
/// - info = "StandbyX3DH"
/// - salt = 32 字节零
fn derive_keys(
    dh1: &[u8; 32],
    dh2: &[u8; 32],
    dh3: &[u8; 32],
    dh4: &[u8; 32],
) -> Result<([u8; 32], [u8; 32], [u8; 32]), CryptoError> {
    // 拼接所有 DH 密钥
    let mut ikm = Vec::with_capacity(128);
    ikm.extend_from_slice(dh1);
    ikm.extend_from_slice(dh2);
    ikm.extend_from_slice(dh3);
    ikm.extend_from_slice(dh4);

    let salt = [0u8; 32];
    let info = b"StandbyX3DH";

    let hk = Hkdf::<Sha256>::new(Some(&salt), &ikm);

    let mut output = [0u8; 96]; // 3 * 32 bytes
    hk.expand(info, &mut output)
        .map_err(|e| CryptoError::KeyDerivation(e.to_string()))?;

    let mut root_key = [0u8; 32];
    let mut chain_key = [0u8; 32];
    let mut associated_data = [0u8; 32];

    root_key.copy_from_slice(&output[0..32]);
    chain_key.copy_from_slice(&output[32..64]);
    associated_data.copy_from_slice(&output[64..96]);

    Ok((root_key, chain_key, associated_data))
}

/// 初始消息 (Alice → Bob)
#[derive(Clone, Serialize, Deserialize)]
pub struct InitialMessage {
    pub identity_key: [u8; 32],        // Alice 的身份公钥
    pub ephemeral_key: [u8; 32],       // Alice 的临时公钥
    pub signed_pre_key_id: u32,        // 使用的 SPK ID
    pub one_time_pre_key_id: Option<u32>,  // 使用的 OPK ID (如果有)
    pub ciphertext: Vec<u8>,           // 加密的第一条消息
    pub nonce: [u8; 12],               // ChaCha20-Poly1305 nonce
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::keys::SigningKeyPair;

    #[test]
    fn test_x3dh_key_agreement() {
        // Alice 生成身份密钥
        let alice_ik = KeyPair::generate();

        // Bob 生成身份密钥和签名密钥
        let bob_ik = KeyPair::generate();
        let _bob_signing = SigningKeyPair::generate();
        let bob_spk = KeyPair::generate();
        let bob_opk = KeyPair::generate();

        // Bob 创建预密钥包
        let bundle = PreKeyBundle {
            identity_key: bob_ik.public.to_bytes(),
            signed_pre_key: bob_spk.public.to_bytes(),
            signed_pre_key_id: 1,
            signed_pre_key_signature: [0u8; 64], // 简化测试
            one_time_pre_key: Some(bob_opk.public.to_bytes()),
            one_time_pre_key_id: Some(1),
        };

        // Alice 发起 X3DH
        let alice_result = x3dh_initiate(&alice_ik, &bundle).unwrap();

        // Bob 响应 X3DH
        let bob_result = x3dh_respond(
            &bob_ik,
            &bob_spk,
            Some(&bob_opk),
            &alice_ik.public.to_bytes(),
            &alice_result.ephemeral_public,
        )
        .unwrap();

        // 双方应得到相同的根密钥和链密钥
        assert_eq!(alice_result.root_key, bob_result.root_key);
        assert_eq!(alice_result.chain_key, bob_result.chain_key);
        assert_eq!(alice_result.associated_data, bob_result.associated_data);
    }

    #[test]
    fn test_x3dh_without_opk() {
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

        let alice_result = x3dh_initiate(&alice_ik, &bundle).unwrap();
        let bob_result = x3dh_respond(
            &bob_ik,
            &bob_spk,
            None,
            &alice_ik.public.to_bytes(),
            &alice_result.ephemeral_public,
        )
        .unwrap();

        assert_eq!(alice_result.root_key, bob_result.root_key);
        assert_eq!(alice_result.chain_key, bob_result.chain_key);
    }
}
