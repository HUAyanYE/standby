//! Standby Resonance gRPC Service
//!
//! 将共鸣计算热路径暴露为 gRPC 服务，供 Python 引擎调用。
//! 使用 tonic + tokio 异步运行时。

use warp::Filter;

// 手动定义 proto 类型 (避免 build.rs 依赖)
// 实际项目中应从 proto 生成

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ComputeResonanceRequest {
    pub user_id: String,
    pub anchor_id: String,
    pub reaction_type: String,
    pub opinion_text: Option<String>,
    pub emotion_word: Option<String>,
    pub opinion_embedding: Vec<f32>,
    pub anchor_embedding: Vec<f32>,
    pub existing_embeddings: Vec<Vec<f32>>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ComputeResonanceResponse {
    pub value: f64,
    pub components: standby_resonance::resonance::ScoreComponents,
}

// 服务实现
pub struct ResonanceService;

impl ResonanceService {
    /// 计算共鸣值 (核心热路径)
    pub async fn compute(
        &self,
        request: ComputeResonanceRequest,
    ) -> Result<ComputeResonanceResponse, String> {
        use standby_resonance::resonance::*;
        use standby_shared::types::*;

        // 解析反应类型
        let reaction_type = match request.reaction_type.as_str() {
            "共鸣" | "RESONANCE" => ReactionType::Resonance,
            "无感" | "NEUTRAL" => ReactionType::Neutral,
            "反对" | "OPPOSITION" => ReactionType::Opposition,
            "未体验" | "UNEXPERIENCED" => ReactionType::Unexperienced,
            "有害" | "HARMFUL" => ReactionType::Harmful,
            _ => return Err(format!("未知反应类型: {}", request.reaction_type)),
        };

        // 解析情感词
        let emotion_word = request.emotion_word.as_deref().and_then(|w| match w {
            "同感" | "EMPATHY" => Some(EmotionWord::Empathy),
            "触发" | "TRIGGER" => Some(EmotionWord::Trigger),
            "启发" | "INSIGHT" => Some(EmotionWord::Insight),
            "震撼" | "SHOCK" => Some(EmotionWord::Shock),
            _ => None,
        });

        let reaction = Reaction {
            user_id: request.user_id,
            anchor_id: request.anchor_id,
            reaction_type,
            opinion_text: request.opinion_text,
            emotion_word,
            timestamp: 0.0,
            harmful_ratio: 0.0,
            unexperienced_ratio: 0.0,
        };

        let anchor = Anchor {
            id: reaction.anchor_id.clone(),
            text: String::new(),
            topics: vec![],
        };

        let result = compute_resonance_value(
            &reaction,
            &anchor,
            &request.opinion_embedding,
            &request.anchor_embedding,
            &request.existing_embeddings,
        );

        match result {
            Some(score) => Ok(ComputeResonanceResponse {
                value: score.value,
                components: ScoreComponents {
                    resonance_weight: score.components.resonance_weight,
                    depth: score.components.depth,
                    relevance_raw: score.components.relevance_raw,
                    relevance_sigmoid: score.components.relevance_sigmoid,
                    novelty: score.components.novelty,
                    harmful_penalty: score.components.harmful_penalty,
                    unexperienced_penalty: score.components.unexperienced_penalty,
                },
            }),
            None => Err("反应类型不计入共鸣值".into()),
        }
    }
}

// HTTP JSON API (替代 gRPC，更简单)
use std::convert::Infallible;

async fn handle_compute(
    body: String,
) -> Result<impl warp::Reply, Infallible> {
    let request: ComputeResonanceRequest = match serde_json::from_str(&body) {
        Ok(r) => r,
        Err(e) => {
            let resp = serde_json::json!({"error": format!("JSON 解析失败: {}", e)});
            return Ok(warp::reply::json(&resp));
        }
    };

    let service = ResonanceService;
    match service.compute(request).await {
        Ok(response) => Ok(warp::reply::json(&response)),
        Err(e) => {
            let resp = serde_json::json!({"error": e});
            Ok(warp::reply::json(&resp))
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 初始化日志
    tracing_subscriber::fmt::init();

    let port: u16 = std::env::var("PORT")
        .unwrap_or_else(|_| "8095".into())
        .parse()?;

    println!("Resonance Service 启动在 0.0.0.0:{}", port);

    // 使用简易 HTTP 服务器 (避免 gRPC 构建复杂度)
    let route = warp::post()
        .and(warp::path("compute"))
        .and(warp::body::bytes().map(|bytes: bytes::Bytes| {
            String::from_utf8_lossy(&bytes).to_string()
        }))
        .and_then(handle_compute);

    warp::serve(route)
        .run(([0, 0, 0, 0], port))
        .await;

    Ok(())
}
