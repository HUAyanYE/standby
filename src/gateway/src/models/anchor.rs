use serde::{Deserialize, Serialize};

/// 生成锚点请求
#[derive(Debug, Deserialize)]
pub struct GenerateAnchorRequest {
    pub source_texts: Vec<String>,
    pub topic_hints: Option<Vec<String>>,
    pub source: Option<String>,
    pub modality: Option<String>,
}

/// 锚点摘要
#[derive(Debug, Serialize)]
pub struct AnchorSummary {
    pub anchor_id: String,
    pub text: String,
    pub topics: Vec<String>,
    pub quality_score: f32,
    pub reaction_count: i32,
    pub created_at: i64,
}

/// 锚点详情
#[derive(Debug, Serialize)]
pub struct AnchorDetail {
    pub anchor_id: String,
    pub text: String,
    pub topics: Vec<String>,
    pub quality_score: f32,
    pub created_at: i64,
}

/// 分页查询参数
#[derive(Debug, Deserialize)]
pub struct PaginationParams {
    pub page: Option<u32>,
    pub page_size: Option<u32>,
    pub topic_filter: Option<String>,
}

/// 感受链节点
#[derive(Debug, Serialize)]
pub struct FeelingChainNode {
    pub reaction_id: String,
    pub user_id: String,
    pub display_name: String,
    pub avatar_seed: String,
    pub text_content: String,
    pub emotion_word: String,
    pub parent_reaction_id: String,
    pub depth: i32,
    pub created_at: i64,
}

/// 群体记忆
#[derive(Debug, Serialize)]
pub struct GroupMemory {
    pub user_opinion_text: String,
    pub resonance_count_at_time: i32,
    pub emotion_words: Vec<String>,
    pub group_evolution: String,
}
