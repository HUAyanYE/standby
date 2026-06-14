//! 共鸣值计算 v2 — 核心算法 (SIMD + 并行优化)

use standby_shared::types::*;
use standby_shared::math::{dot, sigmoid};
use rayon::prelude::*;

// ============================================================
// 反应类型权重 (对齐 PRD)
// ============================================================

/// 获取反应类型权重
pub fn reaction_weight(reaction_type: ReactionType) -> Option<f64> {
    match reaction_type {
        ReactionType::Resonance => Some(1.0),
        ReactionType::Neutral => Some(0.0),
        ReactionType::Opposition => Some(-0.2),
        ReactionType::Unexperienced => None,
        ReactionType::Harmful => None,
    }
}

/// 情绪词加权 (对齐 PRD: 同感×1.0, 触发/启发×1.1, 震撼×1.2)
pub fn emotion_bonus(word: EmotionWord) -> f64 {
    match word {
        EmotionWord::Empathy => 1.0,
        EmotionWord::Trigger => 1.1,
        EmotionWord::Insight => 1.1,
        EmotionWord::Shock => 1.2,
    }
}

/// 反应类型权重 (含情绪词)
pub fn get_resonance_weight(
    reaction_type: ReactionType,
    emotion_word: Option<EmotionWord>,
) -> Option<f64> {
    let base = reaction_weight(reaction_type)?;
    if let (Some(word), ReactionType::Resonance) = (emotion_word, reaction_type) {
        Some(base * emotion_bonus(word))
    } else {
        Some(base)
    }
}

// ============================================================
// v2 核心算法
// ============================================================

/// Sigmoid 相关性过滤 (v2: 替代硬阈值)
///
/// v1: relevance < 0.3 → 0.0 (硬截断)
/// v2: sigmoid(relevance; μ=threshold, k=sharpness)
pub fn sigmoid_relevance(
    relevance: f64,
    threshold: f64,
    sharpness: f64,
) -> f64 {
    sigmoid(sharpness * (relevance - threshold))
}

/// 聚类感知 Novelty (v2: k-NN 均值 + 密度衰减 + 并行计算)
///
/// v1: novelty = 1 - max(sim) 只看最近邻
/// v2: novelty = 1 - mean(top_k_sims) × density_factor
/// v2.1: 使用 rayon 并行计算点积 (多核加速)
pub fn compute_novelty(
    opinion_embedding: &[f32],
    existing_embeddings: &[Vec<f32>],
    relevance: f64,
    k_neighbors: usize,
    relevance_floor: f64,
) -> f64 {
    if relevance < relevance_floor {
        return 0.0;
    }
    if existing_embeddings.len() < 5 {
        return 1.0; // 不惩罚先驱者
    }

    // 并行计算与所有已有观点的相似度
    let mut similarities: Vec<f64> = existing_embeddings
        .par_iter()
        .map(|emb| dot(opinion_embedding, emb) as f64)
        .collect();

    // 取 top-k 相似度的均值
    similarities.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
    let k = k_neighbors.min(similarities.len());
    let mean_top_k: f64 = similarities[..k].iter().sum::<f64>() / k as f64;

    // 密度衰减: 观点越多, novelty 上限越低
    let density_factor =
        1.0 / (1.0 + 0.05 * (existing_embeddings.len() as f64 + 1.0).ln());

    ((1.0 - mean_top_k) * density_factor).max(0.1)
}

/// 复合深度信号 (v2: 字数 × 语义正交性 × 情感强度 × 经历细节)
///
/// v1: 纯字数分档
/// v2: 字数权重 × 语义正交性
/// v2.1: 添加情感强度因子和经历细节因子
pub fn compute_depth(
    text: Option<&str>,
    opinion_embedding: Option<&[f32]>,
    anchor_embedding: Option<&[f32]>,
) -> f64 {
    // 1. 字权重 (使用字符数而非字节数，正确处理中文)
    let base = match text {
        None => 0.6,
        Some(t) if t.trim().is_empty() => 0.6,
        Some(t) if t.chars().count() < 20 => 0.8,
        Some(t) if t.chars().count() < 50 => 0.9,
        Some(t) if t.chars().count() <= 200 => 1.0,
        Some(_) => 1.05,
    };

    // 2. 语义正交性 (可选)
    let semantic_factor = if let (Some(op_emb), Some(an_emb)) = (opinion_embedding, anchor_embedding) {
        let cos_sim = dot(op_emb, an_emb) as f64;
        let orthogonality = 1.0 - cos_sim.abs();
        0.85 + 0.3 * orthogonality
    } else {
        1.0
    };

    // 3. 情感强度因子 (映射到 [0.8, 1.3])
    let emotion_intensity = compute_emotion_intensity(text);
    let emotion_factor = 0.8 + 0.5 * emotion_intensity;

    // 4. 经历细节因子 (映射到 [0.9, 1.2])
    let experience_detail = compute_experience_detail(text);
    let experience_factor = 0.9 + 0.3 * experience_detail;

    base * semantic_factor * emotion_factor * experience_factor
}

/// 计算文本中的情感强度 (0.0 - 1.0)
///
/// 检测维度:
/// 1. 情感关键词匹配
/// 2. 感叹号/问号密度
/// 3. 情感词汇密度
fn compute_emotion_intensity(text: Option<&str>) -> f64 {
    let text = match text {
        None => return 0.0,
        Some(t) if t.trim().is_empty() => return 0.0,
        Some(t) => t,
    };

    let mut score: f64 = 0.0;

    // 1. 情感关键词匹配
    let high_keywords = ["震撼", "崩溃", "泪流满面", "无法呼吸", "心碎", "绝望", "狂喜",
                         "热泪盈眶", "刻骨铭心", "终身难忘", "永生难忘", "改变人生", "颠覆认知"];
    let medium_keywords = ["感动", "触动", "感慨", "难过", "开心", "激动", "怀念", "思念",
                           "温暖", "心酸", "欣慰", "释然", "顿悟", "觉醒"];
    let low_keywords = ["还好", "一般", "普通", "还行", "没什么", "无所谓", "随便"];

    for keyword in &high_keywords {
        if text.contains(keyword) {
            score += 0.3;
        }
    }
    for keyword in &medium_keywords {
        if text.contains(keyword) {
            score += 0.15;
        }
    }
    for keyword in &low_keywords {
        if text.contains(keyword) {
            score -= 0.1;
        }
    }

    // 2. 感叹号/问号密度
    let exclamation_count = text.matches('！').count() as f64 + text.matches('!').count() as f64;
    let question_count = text.matches('？').count() as f64 + text.matches('?').count() as f64;
    let punctuation_density = (exclamation_count + question_count) / text.len().max(1) as f64;
    score += (punctuation_density * 10.0).min(0.2);

    // 3. 情感词汇密度 (形容词后缀)
    let adj_suffixes = ["的", "地", "得", "了", "着", "过"];
    let adj_count: f64 = adj_suffixes.iter()
        .map(|suffix| text.matches(suffix).count() as f64)
        .sum();
    let adj_density = adj_count / text.len().max(1) as f64;
    score += (adj_density * 5.0).min(0.2);

    score.clamp(0.0, 1.0)
}

/// 计算文本中的经历细节程度 (0.0 - 1.0)
///
/// 检测维度:
/// 1. 经历细节关键词
/// 2. 时间/地点标记
/// 3. 人称代词使用
fn compute_experience_detail(text: Option<&str>) -> f64 {
    let text = match text {
        None => return 0.0,
        Some(t) if t.trim().is_empty() => return 0.0,
        Some(t) => t,
    };

    let mut score: f64 = 0.0;

    // 1. 经历细节关键词
    let detail_keywords = ["有一次", "记得", "曾经", "那年", "小时候", "第一次", "最后一次",
                           "那天", "当时", "后来", "从此", "从此以后", "直到现在", "至今",
                           "在我", "我在", "我们", "我的", "他的", "她的"];
    let detail_count = detail_keywords.iter()
        .filter(|k| text.contains(*k))
        .count() as f64;
    score += (detail_count * 0.1).min(0.5);

    // 2. 时间/地点标记
    let time_markers = ["年", "月", "日", "时", "分", "秒", "早上", "中午", "下午", "晚上",
                        "凌晨", "深夜", "傍晚", "黄昏", "黎明"];
    let time_count = time_markers.iter()
        .filter(|m| text.contains(*m))
        .count() as f64;
    score += (time_count * 0.1).min(0.3);

    // 3. 人称代词使用 (表示个人视角)
    let personal_pronouns = ["我", "你", "他", "她", "我们", "你们", "他们"];
    let pronoun_count: f64 = personal_pronouns.iter()
        .map(|p| text.matches(p).count() as f64)
        .sum();
    let pronoun_density = pronoun_count / text.len().max(1) as f64;
    score += (pronoun_density * 10.0).min(0.2);

    score.clamp(0.0, 1.0)
}

/// 完整共鸣值计算 (v2)
pub fn compute_resonance_value(
    reaction: &Reaction,
    _anchor: &Anchor,
    opinion_embedding: &[f32],
    anchor_embedding: &[f32],
    existing_embeddings: &[Vec<f32>],
) -> Option<ResonanceScore> {
    // 1. 反应类型权重
    let resonance_weight = get_resonance_weight(reaction.reaction_type, reaction.emotion_word)?;

    // 2. 判断是否有文字
    let has_text = reaction.opinion_text.as_ref().map_or(false, |t| !t.trim().is_empty());

    let (relevance, novelty, depth) = if has_text {
        let rel_raw = dot(opinion_embedding, anchor_embedding) as f64;
        let rel = sigmoid_relevance(rel_raw, 0.3, 15.0);
        let nov = compute_novelty(opinion_embedding, existing_embeddings, rel_raw, 5, 0.3);
        let dep = compute_depth(
            reaction.opinion_text.as_deref(),
            Some(opinion_embedding),
            Some(anchor_embedding),
        );
        (rel, nov, dep)
    } else {
        (1.0, 1.0, 0.6)
    };

    // 3. 惩罚系数 (指数型)
    let harmful_pen = super::penalty::harmful_penalty(reaction.harmful_ratio);
    let unexp_pen = super::penalty::unexperienced_penalty(reaction.unexperienced_ratio);

    // 4. 最终值
    let value = resonance_weight * depth * relevance * novelty * harmful_pen * unexp_pen;

    Some(ResonanceScore {
        value,
        components: ScoreComponents {
            resonance_weight,
            depth,
            relevance_raw: if has_text { dot(opinion_embedding, anchor_embedding) as f64 } else { 1.0 },
            relevance_sigmoid: relevance,
            novelty,
            harmful_penalty: harmful_pen,
            unexperienced_penalty: unexp_pen,
        },
    })
}

/// 共鸣值结果
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ResonanceScore {
    pub value: f64,
    pub components: ScoreComponents,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ScoreComponents {
    pub resonance_weight: f64,
    pub depth: f64,
    pub relevance_raw: f64,
    pub relevance_sigmoid: f64,
    pub novelty: f64,
    pub harmful_penalty: f64,
    pub unexperienced_penalty: f64,
}

// ============================================================
// 测试
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    fn make_reaction(
        reaction_type: ReactionType,
        emotion: Option<EmotionWord>,
        text: Option<&str>,
    ) -> Reaction {
        Reaction {
            user_id: "u1".into(),
            anchor_id: "a1".into(),
            reaction_type,
            opinion_text: text.map(String::from),
            emotion_word: emotion,
            timestamp: 0.0,
            harmful_ratio: 0.0,
            unexperienced_ratio: 0.0,
        }
    }

    fn make_anchor() -> Anchor {
        Anchor {
            id: "a1".into(),
            text: "深夜独自坐在末班地铁上".into(),
            topics: vec!["孤独".into(), "城市".into()],
        }
    }

    fn fake_embedding(seed: f32) -> Vec<f32> {
        // 生成假向量用于测试 (非归一化, 仅用于逻辑验证)
        let mut v: Vec<f32> = (0..768).map(|i| ((i as f32 + seed) * 0.01).sin()).collect();
        let norm: f32 = v.iter().map(|x| x * x).sum::<f32>().sqrt();
        for x in v.iter_mut() {
            *x /= norm;
        }
        v
    }

    #[test]
    fn test_reaction_weights() {
        assert_eq!(reaction_weight(ReactionType::Resonance), Some(1.0));
        assert_eq!(reaction_weight(ReactionType::Neutral), Some(0.0));
        assert_eq!(reaction_weight(ReactionType::Opposition), Some(-0.2));
        assert_eq!(reaction_weight(ReactionType::Harmful), None);
        assert_eq!(reaction_weight(ReactionType::Unexperienced), None);
    }

    #[test]
    fn test_emotion_bonuses() {
        assert_eq!(emotion_bonus(EmotionWord::Empathy), 1.0);
        assert_eq!(emotion_bonus(EmotionWord::Trigger), 1.1);
        assert_eq!(emotion_bonus(EmotionWord::Insight), 1.1);
        assert_eq!(emotion_bonus(EmotionWord::Shock), 1.2);
    }

    #[test]
    fn test_depth_medium_text() {
        // "字".repeat(100) = 100 chars, 300 bytes > 200 → base=1.05
        // 无情感词/经历词 → emotion_factor=0.8, experience_factor=0.9
        // depth = 1.05 * 1.0 * 0.8 * 0.9 = 0.756
        let d = compute_depth(Some(&"字".repeat(100)), None, None);
        assert!((d - 0.756).abs() < 0.01, "100个中文字符无情感词, depth应为0.756, got {}", d);
    }

    #[test]
    fn test_sigmoid_relevance() {
        // 阈值处 = 0.5
        let at_threshold = sigmoid_relevance(0.3, 0.3, 15.0);
        assert!((at_threshold - 0.5).abs() < 0.001);

        // 远高于阈值 ≈ 1.0
        let high = sigmoid_relevance(0.9, 0.3, 15.0);
        assert!(high > 0.99);

        // 远低于阈值 ≈ 0.0 (sigmoid(-3.0) ≈ 0.0474)
        let low = sigmoid_relevance(0.1, 0.3, 15.0);
        assert!(low < 0.05, "sigmoid(-3.0) ≈ 0.0474, 应 < 0.05");
    }

    #[test]
    fn test_novelty_insufficient_data() {
        let emb = fake_embedding(1.0);
        let existing = vec![fake_embedding(2.0), fake_embedding(3.0)];
        // < 5 条, 应返回 1.0
        let nov = compute_novelty(&emb, &existing, 0.5, 5, 0.3);
        assert_eq!(nov, 1.0);
    }

    #[test]
    fn test_novelty_low_relevance() {
        let emb = fake_embedding(1.0);
        let existing: Vec<_> = (0..10).map(|i| fake_embedding(i as f32)).collect();
        let nov = compute_novelty(&emb, &existing, 0.1, 5, 0.3);
        assert_eq!(nov, 0.0);
    }

    #[test]
    fn test_depth_no_text() {
        // base=0.6, semantic=1.0, emotion=0.8, experience=0.9
        // depth = 0.6 * 1.0 * 0.8 * 0.9 = 0.432
        let d = compute_depth(None, None, None);
        assert!((d - 0.432).abs() < 0.01, "无文本 depth 应为 0.432, got {}", d);
    }

    #[test]
    fn test_depth_short_text() {
        // "短" = 3 bytes < 20 → base=0.8
        // 无情感词/经历词 → emotion=0.8, experience=0.9
        // depth = 0.8 * 1.0 * 0.8 * 0.9 = 0.576
        let d = compute_depth(Some("短"), None, None);
        assert!((d - 0.576).abs() < 0.01, "短文本 depth 应为 0.576, got {}", d);
    }

    #[test]
    fn test_harmful_blocked() {
        let reaction = make_reaction(ReactionType::Harmful, None, None);
        let anchor = make_anchor();
        let emb = fake_embedding(1.0);
        let result = compute_resonance_value(&reaction, &anchor, &emb, &emb, &[]);
        assert!(result.is_none(), "Harmful 不应计入共鸣值");
    }

    #[test]
    fn test_unexperienced_blocked() {
        let reaction = make_reaction(ReactionType::Unexperienced, None, None);
        let anchor = make_anchor();
        let emb = fake_embedding(1.0);
        let result = compute_resonance_value(&reaction, &anchor, &emb, &emb, &[]);
        assert!(result.is_none(), "未体验不应计入共鸣值");
    }

    #[test]
    fn test_resonance_click_only() {
        let reaction = make_reaction(ReactionType::Resonance, Some(EmotionWord::Empathy), None);
        let anchor = make_anchor();
        let emb = fake_embedding(1.0);
        let score = compute_resonance_value(&reaction, &anchor, &emb, &emb, &[]).unwrap();

        // 纯点击: weight=1.0, depth=0.432, relevance=1.0, novelty=1.0
        // value = 1.0 * 0.432 * 1.0 * 1.0 = 0.432
        assert!((score.value - 0.432).abs() < 0.01, "纯点击共鸣值应为 0.432, got {}", score.value);
    }

    #[test]
    fn test_resonance_with_opinion() {
        let reaction = make_reaction(
            ReactionType::Resonance,
            Some(EmotionWord::Shock),
            Some("孤独不是身边没有人，是没有人知道你在哪里。"),
        );
        let anchor = make_anchor();
        let emb = fake_embedding(1.0);
        let score = compute_resonance_value(&reaction, &anchor, &emb, &emb, &[]).unwrap();

        // 震撼×1.2, 有文字, novelty=1.0 (无已有观点)
        assert!(score.value > 0.5, "有观点的共鸣值应大于纯点击");
        assert!(score.components.novelty > 0.99, "先驱者 novelty 应为 1.0");
    }

    #[test]
    fn test_opposition_negative() {
        let reaction = make_reaction(ReactionType::Opposition, None, Some("我不觉得这是孤独。"));
        let anchor = make_anchor();
        let emb = fake_embedding(1.0);
        let score = compute_resonance_value(&reaction, &anchor, &emb, &emb, &[]).unwrap();
        assert!(score.value < 0.0, "反对应为负值");
    }

    #[test]
    fn test_emotion_intensity_high() {
        let intensity = compute_emotion_intensity(Some("我泪流满面，心碎了"));
        assert!(intensity > 0.3, "高情感文本应 > 0.3, got {}", intensity);
    }

    #[test]
    fn test_emotion_intensity_none() {
        let intensity = compute_emotion_intensity(None);
        assert_eq!(intensity, 0.0);
    }

    #[test]
    fn test_experience_detail_high() {
        let detail = compute_experience_detail(Some("记得那年小时候，我第一次看到雪"));
        assert!(detail > 0.3, "高经历细节应 > 0.3, got {}", detail);
    }

    #[test]
    fn test_experience_detail_none() {
        let detail = compute_experience_detail(None);
        assert_eq!(detail, 0.0);
    }

    #[test]
    fn test_depth_with_emotion() {
        // 包含情感词的文本，depth 应更高
        let d_neutral = compute_depth(Some("这个观点很好"), None, None);
        let d_emotional = compute_depth(Some("这个观点让我泪流满面，震撼！"), None, None);
        assert!(d_emotional > d_neutral, "情感文本 depth 应更高: {} vs {}", d_emotional, d_neutral);
    }
}
