use serde::{Deserialize, Serialize};

/// 提交情境状态请求
#[derive(Debug, Deserialize)]
pub struct SubmitContextRequest {
    pub scene_type: String,
    pub mood_hint: Option<String>,
    pub attention_level: Option<String>,
    pub active_device: Option<i32>,
}

/// 情境权重查询参数
#[derive(Debug, Deserialize)]
pub struct ContextualWeightsParams {
    pub topics: String, // 逗号分隔的话题列表
}

/// 情境权重响应
#[derive(Debug, Serialize)]
pub struct ContextualWeights {
    pub topic_weights: std::collections::HashMap<String, f32>,
    pub recommended_scene: String,
}

/// 文本编码请求
#[derive(Debug, Deserialize)]
pub struct EncodeTextRequest {
    pub texts: Vec<String>,
}

/// 文本编码响应
#[derive(Debug, Serialize)]
pub struct EncodeTextResponse {
    pub vectors: Vec<Vec<u8>>,
    pub dimension: i32,
}
