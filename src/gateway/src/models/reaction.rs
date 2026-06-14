use serde::{Deserialize, Serialize};

/// 反应类型枚举
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReactionType {
    Resonance = 1,      // 共鸣
    Indifference = 2,   // 无感
    Opposition = 3,     // 反对
    Unexperienced = 4,  // 未体验
    Harmful = 5,        // 有害
}

impl ReactionType {
    pub fn from_i32(value: i32) -> Option<Self> {
        match value {
            1 => Some(Self::Resonance),
            2 => Some(Self::Indifference),
            3 => Some(Self::Opposition),
            4 => Some(Self::Unexperienced),
            5 => Some(Self::Harmful),
            _ => None,
        }
    }
}

/// 情感词枚举
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EmotionWord {
    Sympathy = 1,   // 同感
    Trigger = 2,    // 触发
    Inspire = 3,    // 启发
    Shock = 4,      // 震撼
}

impl EmotionWord {
    pub fn from_i32(value: i32) -> Option<Self> {
        match value {
            1 => Some(Self::Sympathy),
            2 => Some(Self::Trigger),
            3 => Some(Self::Inspire),
            4 => Some(Self::Shock),
            _ => None,
        }
    }
}

/// 批量请求最大大小
const MAX_BATCH_SIZE: usize = 100;

/// 提交反应请求
#[derive(Debug, Deserialize)]
pub struct ProcessReactionRequest {
    pub anchor_id: String,
    pub reaction_type: i32,
    pub opinion_text: Option<String>,
    pub opinion_vector: Option<Vec<u8>>,
    pub emotion_word: Option<i32>,
    pub parent_reaction_id: Option<String>,
}

impl ProcessReactionRequest {
    pub fn validate(&self) -> Result<(), String> {
        if self.anchor_id.is_empty() {
            return Err("anchor_id 不能为空".into());
        }
        if ReactionType::from_i32(self.reaction_type).is_none() {
            return Err(format!("无效的 reaction_type: {}，有效值为 1-5", self.reaction_type));
        }
        if let Some(ew) = self.emotion_word {
            if EmotionWord::from_i32(ew).is_none() {
                return Err(format!("无效的 emotion_word: {}，有效值为 1-4", ew));
            }
        }
        if let Some(ref text) = self.opinion_text {
            if text.len() > 5000 {
                return Err("opinion_text 长度不能超过 5000 字符".into());
            }
        }
        Ok(())
    }
}

/// 批量反应请求
#[derive(Debug, Deserialize)]
pub struct ProcessBatchRequest {
    pub batch_id: String,
    pub reactions: Vec<ProcessReactionRequest>,
}

impl ProcessBatchRequest {
    pub fn validate(&self) -> Result<(), String> {
        if self.reactions.is_empty() {
            return Err("reactions 不能为空".into());
        }
        if self.reactions.len() > MAX_BATCH_SIZE {
            return Err(format!("批量大小不能超过 {}，当前: {}", MAX_BATCH_SIZE, self.reactions.len()));
        }
        for (i, r) in self.reactions.iter().enumerate() {
            r.validate().map_err(|e| format!("reactions[{}]: {}", i, e))?;
        }
        Ok(())
    }
}

/// 反应结果
#[derive(Debug, Serialize)]
pub struct ReactionResult {
    pub success: bool,
    pub event_id: String,
    pub resonance_value: f32,
    pub relationship_score: f32,
    pub related_user_id: String,
    pub processing_time_ms: f32,
}

/// 批量结果
#[derive(Debug, Serialize)]
pub struct BatchResult {
    pub success: bool,
    pub batch_id: String,
    pub total_processed: i32,
    pub total_errors: i32,
}

/// 反应项
#[derive(Debug, Serialize)]
pub struct ReactionItem {
    pub reaction_id: String,
    pub user_id: String,
    pub reaction_type: i32,
    pub emotion_word: i32,
    pub opinion_text: String,
    pub resonance_value: f32,
    pub created_at: i64,
}

/// 反应分布
#[derive(Debug, Serialize)]
pub struct ReactionDistribution {
    pub resonance_count: i32,
    pub neutral_count: i32,
    pub opposition_count: i32,
    pub unexperienced_count: i32,
    pub harmful_count: i32,
    pub total_count: i32,
}

/// 关系分
#[derive(Debug, Serialize)]
pub struct RelationshipScore {
    pub found: bool,
    pub score_a_to_b: f32,
    pub score_b_to_a: f32,
    pub topic_diversity: i32,
    pub resonance_count: i32,
}

/// 共鸣对
#[derive(Debug, Serialize)]
pub struct ResonancePair {
    pub other_user_id: String,
    pub relationship_score: f32,
    pub shared_anchors: i32,
}

/// 列表查询参数
#[derive(Debug, Deserialize)]
pub struct ReactionListParams {
    pub page: Option<u32>,
    pub page_size: Option<u32>,
    pub filter_type: Option<String>,
}

impl ReactionListParams {
    pub fn validated_page_size(&self) -> u32 {
        self.page_size.unwrap_or(20).min(100)
    }

    pub fn validated_page(&self) -> u32 {
        self.page.unwrap_or(1).max(1)
    }
}
