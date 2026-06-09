use serde::{Deserialize, Serialize};

/// 提交反应请求
#[derive(Debug, Deserialize)]
pub struct ProcessReactionRequest {
    pub anchor_id: String,
    pub reaction_type: i32,         // 1=共鸣 2=无感 3=反对 4=未体验 5=有害
    pub opinion_text: Option<String>,
    pub opinion_vector: Option<Vec<u8>>,
    pub emotion_word: Option<i32>,  // 1=同感 2=触发 3=启发 4=震撼
    pub parent_reaction_id: Option<String>,
}

/// 批量反应请求
#[derive(Debug, Deserialize)]
pub struct ProcessBatchRequest {
    pub batch_id: String,
    pub reactions: Vec<ProcessReactionRequest>,
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
