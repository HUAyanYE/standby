//! 共享数据类型 — 对齐 proto/common/common.proto

use serde::{Deserialize, Serialize};

/// 五态反应类型 (PRD §3.2)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ReactionType {
    Resonance,      // 共鸣
    Neutral,        // 无感
    Opposition,     // 反对
    Unexperienced,  // 未体验
    Harmful,        // 有害
}

/// 共鸣情绪词 (PRD §3.2)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum EmotionWord {
    Empathy,   // 同感
    Trigger,   // 触发
    Insight,   // 启发
    Shock,     // 震撼
}

/// 信任级别 (PRD §4.2)
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum TrustLevel {
    L0Browse = 0,
    L1TraceVisible = 1,
    L2OpinionReply = 2,
    L3AsyncMessage = 3,
    L4RealtimeChat = 4,
    L5GroupChat = 5,
}

/// 治理级别
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GovernanceLevel {
    Normal,
    Observing,
    Demoted,
    Suspended,
    Removed,
    Conflict,
}

impl std::fmt::Display for GovernanceLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Normal => write!(f, "L0_正常"),
            Self::Observing => write!(f, "L1_观察"),
            Self::Demoted => write!(f, "L2_降权"),
            Self::Suspended => write!(f, "L3_暂停"),
            Self::Removed => write!(f, "L4_移除"),
            Self::Conflict => write!(f, "争议"),
        }
    }
}

/// 用户反应
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Reaction {
    pub user_id: String,
    pub anchor_id: String,
    pub reaction_type: ReactionType,
    pub opinion_text: Option<String>,
    pub emotion_word: Option<EmotionWord>,
    pub timestamp: f64,
    pub harmful_ratio: f64,
    pub unexperienced_ratio: f64,
}

/// 锚点
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Anchor {
    pub id: String,
    pub text: String,
    pub topics: Vec<String>,
}

/// 反应统计
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContentReaction {
    pub anchor_id: String,
    pub resonance: u32,
    pub neutral: u32,
    pub opposition: u32,
    pub unexperienced: u32,
    pub harmful: u32,
}

impl ContentReaction {
    pub fn total(&self) -> u32 {
        self.resonance + self.neutral + self.opposition + self.unexperienced + self.harmful
    }

    pub fn harmful_ratio(&self) -> f64 {
        self.harmful as f64 / self.total().max(1) as f64
    }

    pub fn unexperienced_ratio(&self) -> f64 {
        self.unexperienced as f64 / self.total().max(1) as f64
    }

    pub fn resonance_ratio(&self) -> f64 {
        self.resonance as f64 / self.total().max(1) as f64
    }
}

/// 标记者记录
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarkerRecord {
    pub token_hash: String,
    pub credit_score: f64,
    pub total_marks: u32,
    pub accurate_marks: u32,
    pub last_mark_ts: f64,
}

impl MarkerRecord {
    pub fn new(token_hash: String) -> Self {
        Self {
            token_hash,
            credit_score: 0.5,
            total_marks: 0,
            accurate_marks: 0,
            last_mark_ts: 0.0,
        }
    }
}
