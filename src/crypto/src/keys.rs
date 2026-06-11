//! 密钥类型定义
//!
//! Signal 协议使用以下密钥:
//! - Identity Key (IK): 长期身份密钥 (X25519)
//! - Signed Pre Key (SPK): 签名预密钥 (X25519 + Ed25519 签名)
//! - One-Time Pre Key (OPK): 一次性预密钥 (X25519)
//! - Ephemeral Key (EK): 临时密钥 (X25519)
//! - Ratchet Key: 棘轮密钥 (X25519, 每轮更新)

use serde::{Deserialize, Serialize};
use serde_big_array::BigArray;
use x25519_dalek::{StaticSecret, PublicKey};
use ed25519_dalek::{SigningKey, VerifyingKey, Signature, Signer, Verifier};
use rand::rngs::OsRng;

use crate::error::CryptoError;

/// 密钥对 (私钥 + 公钥)
#[derive(Clone)]
pub struct KeyPair {
    pub secret: StaticSecret,
    pub public: PublicKey,
}

impl KeyPair {
    /// 生成新的随机密钥对
    pub fn generate() -> Self {
        let secret = StaticSecret::random_from_rng(OsRng);
        let public = PublicKey::from(&secret);
        Self { secret, public }
    }

    /// 从字节恢复私钥
    pub fn from_bytes(bytes: &[u8; 32]) -> Self {
        let secret = StaticSecret::from(*bytes);
        let public = PublicKey::from(&secret);
        Self { secret, public }
    }

    /// 执行 Diffie-Hellman 密钥交换
    pub fn diffie_hellman(&self, their_public: &PublicKey) -> [u8; 32] {
        self.secret.diffie_hellman(their_public).to_bytes()
    }
}

/// 身份密钥 (长期)
#[derive(Clone, Serialize)]
pub struct IdentityKey {
    /// 公钥 (可公开)
    pub public_key: [u8; 32],
    /// 私钥 (保密, 仅端侧存储)
    #[serde(skip)]
    secret_key: Option<[u8; 32]>,
}

// 手动实现 Deserialize (跳过 secret_key)
impl<'de> Deserialize<'de> for IdentityKey {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        #[derive(Deserialize)]
        struct IdentityKeyPublic {
            public_key: [u8; 32],
        }
        let raw = IdentityKeyPublic::deserialize(deserializer)?;
        Ok(Self {
            public_key: raw.public_key,
            secret_key: None,
        })
    }
}

impl IdentityKey {
    /// 生成新的身份密钥
    pub fn generate() -> Self {
        let kp = KeyPair::generate();
        Self {
            public_key: kp.public.to_bytes(),
            secret_key: Some(kp.secret.to_bytes()),
        }
    }

    /// 从公钥创建 (仅公钥, 用于验证对方)
    pub fn from_public(public_key: [u8; 32]) -> Self {
        Self {
            public_key,
            secret_key: None,
        }
    }

    /// 获取私钥 (如果有)
    pub fn secret(&self) -> Option<&[u8; 32]> {
        self.secret_key.as_ref()
    }

    /// 获取 KeyPair (如果有私钥)
    pub fn keypair(&self) -> Option<KeyPair> {
        self.secret_key.map(|bytes| KeyPair::from_bytes(&bytes))
    }

    /// 获取公钥
    pub fn public(&self) -> PublicKey {
        PublicKey::from(self.public_key)
    }
}

/// 签名预密钥
#[derive(Clone, Serialize)]
pub struct SignedPreKey {
    pub key_id: u32,
    pub public_key: [u8; 32],
    #[serde(with = "BigArray")]
    pub signature: [u8; 64],
    #[serde(skip)]
    secret_key: Option<[u8; 32]>,
}

impl<'de> Deserialize<'de> for SignedPreKey {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        #[derive(Deserialize)]
        struct SignedPreKeyPublic {
            key_id: u32,
            public_key: [u8; 32],
            #[serde(with = "BigArray")]
            signature: [u8; 64],
        }
        let raw = SignedPreKeyPublic::deserialize(deserializer)?;
        Ok(Self {
            key_id: raw.key_id,
            public_key: raw.public_key,
            signature: raw.signature,
            secret_key: None,
        })
    }
}

impl SignedPreKey {
    /// 生成新的签名预密钥
    pub fn generate(key_id: u32, identity_signing_key: &SigningKey) -> Self {
        let kp = KeyPair::generate();
        let signature = identity_signing_key.sign(kp.public.as_bytes());

        Self {
            key_id,
            public_key: kp.public.to_bytes(),
            signature: signature.to_bytes(),
            secret_key: Some(kp.secret.to_bytes()),
        }
    }

    /// 验证签名
    pub fn verify_signature(&self, identity_verifying_key: &VerifyingKey) -> bool {
        let Ok(sig) = Signature::from_slice(&self.signature) else {
            return false;
        };
        identity_verifying_key.verify(&self.public_key, &sig).is_ok()
    }

    /// 获取私钥 (如果有)
    pub fn secret(&self) -> Option<&[u8; 32]> {
        self.secret_key.as_ref()
    }

    /// 获取 KeyPair
    pub fn keypair(&self) -> Option<KeyPair> {
        self.secret_key.map(|bytes| KeyPair::from_bytes(&bytes))
    }
}

/// 一次性预密钥
#[derive(Clone, Serialize)]
pub struct OneTimePreKey {
    pub key_id: u32,
    pub public_key: [u8; 32],
    #[serde(skip)]
    secret_key: Option<[u8; 32]>,
}

impl<'de> Deserialize<'de> for OneTimePreKey {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        #[derive(Deserialize)]
        struct OneTimePreKeyPublic {
            key_id: u32,
            public_key: [u8; 32],
        }
        let raw = OneTimePreKeyPublic::deserialize(deserializer)?;
        Ok(Self {
            key_id: raw.key_id,
            public_key: raw.public_key,
            secret_key: None,
        })
    }
}

impl OneTimePreKey {
    /// 生成新的一次性预密钥
    pub fn generate(key_id: u32) -> Self {
        let kp = KeyPair::generate();
        Self {
            key_id,
            public_key: kp.public.to_bytes(),
            secret_key: Some(kp.secret.to_bytes()),
        }
    }

    /// 获取私钥 (如果有)
    pub fn secret(&self) -> Option<&[u8; 32]> {
        self.secret_key.as_ref()
    }

    /// 获取 KeyPair
    pub fn keypair(&self) -> Option<KeyPair> {
        self.secret_key.map(|bytes| KeyPair::from_bytes(&bytes))
    }
}

/// 临时密钥
#[derive(Clone)]
pub struct EphemeralKey {
    pub keypair: KeyPair,
}

impl EphemeralKey {
    pub fn generate() -> Self {
        Self {
            keypair: KeyPair::generate(),
        }
    }
}

/// 棘轮密钥 (每轮更新)
#[derive(Clone)]
pub struct RatchetKey {
    pub keypair: KeyPair,
    pub generation: u32,
}

impl RatchetKey {
    pub fn generate() -> Self {
        Self {
            keypair: KeyPair::generate(),
            generation: 0,
        }
    }

    /// 轮换到下一个密钥
    pub fn rotate(&mut self) {
        self.keypair = KeyPair::generate();
        self.generation += 1;
    }
}

/// 签名密钥对 (Ed25519, 用于签名预密钥)
pub struct SigningKeyPair {
    pub signing_key: SigningKey,
    pub verifying_key: VerifyingKey,
}

impl SigningKeyPair {
    pub fn generate() -> Self {
        let signing_key = SigningKey::generate(&mut OsRng);
        let verifying_key = signing_key.verifying_key();
        Self {
            signing_key,
            verifying_key,
        }
    }

    /// 从字节恢复
    pub fn from_bytes(bytes: &[u8; 32]) -> Result<Self, CryptoError> {
        let signing_key = SigningKey::from_bytes(bytes);
        let verifying_key = signing_key.verifying_key();
        Ok(Self {
            signing_key,
            verifying_key,
        })
    }
}
