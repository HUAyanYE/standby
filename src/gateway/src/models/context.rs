use serde::{Deserialize, Serialize};

/// 文本编码请求最大大小
const MAX_ENCODE_TEXTS: usize = 50;
const MAX_TEXT_LENGTH: usize = 10000;

/// 提交情境状态请求
#[derive(Debug, Deserialize)]
pub struct SubmitContextRequest {
    pub scene_type: String,
    pub mood_hint: Option<String>,
    pub attention_level: Option<String>,
    pub active_device: Option<i32>,
}

impl SubmitContextRequest {
    pub fn validate(&self) -> Result<(), String> {
        if self.scene_type.is_empty() {
            return Err("scene_type 不能为空".into());
        }
        if self.scene_type.len() > 50 {
            return Err("scene_type 长度不能超过 50 字符".into());
        }
        Ok(())
    }
}

/// 情境权重查询参数
#[derive(Debug, Deserialize)]
pub struct ContextualWeightsParams {
    pub topics: String,
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

impl EncodeTextRequest {
    pub fn validate(&self) -> Result<(), String> {
        if self.texts.is_empty() {
            return Err("texts 不能为空".into());
        }
        if self.texts.len() > MAX_ENCODE_TEXTS {
            return Err(format!("texts 数量不能超过 {}，当前: {}", MAX_ENCODE_TEXTS, self.texts.len()));
        }
        for (i, text) in self.texts.iter().enumerate() {
            if text.is_empty() {
                return Err(format!("texts[{}] 不能为空字符串", i));
            }
            if text.len() > MAX_TEXT_LENGTH {
                return Err(format!("texts[{}] 长度不能超过 {} 字符", i, MAX_TEXT_LENGTH));
            }
        }
        Ok(())
    }
}

/// 文本编码响应
#[derive(Debug, Serialize)]
pub struct EncodeTextResponse {
    pub vectors: Vec<Vec<u8>>,
    pub dimension: i32,
}
