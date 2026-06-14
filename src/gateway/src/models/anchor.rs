use serde::{Deserialize, Serialize};

/// 分页参数最大值
const MAX_PAGE_SIZE: u32 = 100;
const MAX_FEELING_CHAIN_DEPTH: i32 = 5;

/// 生成锚点请求
#[derive(Debug, Deserialize)]
pub struct GenerateAnchorRequest {
    pub source_texts: Vec<String>,
    pub topic_hints: Option<Vec<String>>,
    pub source: Option<String>,
    pub modality: Option<String>,
}

impl GenerateAnchorRequest {
    pub fn validate(&self) -> Result<(), String> {
        if self.source_texts.is_empty() {
            return Err("source_texts 不能为空".into());
        }
        for (i, text) in self.source_texts.iter().enumerate() {
            if text.trim().is_empty() {
                return Err(format!("source_texts[{}] 不能为空白", i));
            }
            if text.len() > 10000 {
                return Err(format!("source_texts[{}] 长度不能超过 10000 字符", i));
            }
        }
        Ok(())
    }
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

impl PaginationParams {
    pub fn validated_page_size(&self) -> u32 {
        self.page_size.unwrap_or(20).min(MAX_PAGE_SIZE)
    }

    pub fn validated_page(&self) -> u32 {
        self.page.unwrap_or(1).max(1)
    }
}

/// 感受链查询参数
#[derive(Debug, Deserialize)]
pub struct FeelingChainParams {
    pub max_depth: Option<i32>,
}

impl FeelingChainParams {
    pub fn validated_max_depth(&self) -> i32 {
        self.max_depth.unwrap_or(3).min(MAX_FEELING_CHAIN_DEPTH).max(1)
    }
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
