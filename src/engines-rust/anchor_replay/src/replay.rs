//! 锚点重现 v2 — 多因子触发评分

use std::collections::HashMap;

/// 重现触发类型
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReplayTrigger {
    Seasonal,
    Anniversary,
    SocialEvent,
    ClassicCycle,
    GroupMemory,
}

/// 重现候选
#[derive(Debug, Clone)]
pub struct ReplayCandidate {
    pub anchor_id: String,
    pub topics: Vec<String>,
    pub trigger_type: ReplayTrigger,
    pub last_shown_ts: f64,
    pub show_count: u32,
}

/// 群体记忆数据
#[derive(Debug, Clone)]
pub struct GroupMemoryData {
    pub total_reactions: u32,
    pub resonance_count: u32,
}

/// 用户亲和度
///
/// 用户在锚点话题上的历史参与度
pub fn compute_user_affinity(
    user_topic_history: &HashMap<String, u32>,
    anchor_topics: &[String],
) -> f64 {
    let total: u32 = user_topic_history.values().sum();
    if total == 0 {
        return 0.5;
    }

    let match_count: u32 = anchor_topics
        .iter()
        .map(|t| user_topic_history.get(t).copied().unwrap_or(0))
        .sum();

    0.5 + (match_count as f64 / total as f64)
}

/// 获取当前季节
pub fn get_current_season(month: u32) -> &'static str {
    match month {
        3..=5 => "spring",
        6..=8 => "summer",
        9..=11 => "autumn",
        _ => "winter",
    }
}

/// 季节关键词匹配 (简化版, 生产环境可用语义匹配)
pub fn seasonal_relevance(topics: &[String], season: &str) -> f64 {
    let keywords: &[&str] = match season {
        "spring" => &["春天", "花开", "新生", "希望"],
        "summer" => &["夏天", "毕业", "旅行", "海边"],
        "autumn" => &["秋天", "落叶", "收获", "中秋"],
        "winter" => &["冬天", "雪", "新年", "春节"],
        _ => return 0.0,
    };

    let matches = topics
        .iter()
        .filter(|t| keywords.iter().any(|k| t.contains(k)))
        .count();

    (matches as f64 / 2.0).min(1.0)
}

/// 多因子触发评分 v2
///
/// v1: score = decay × freq_penalty × trigger_weight × season_bonus (乘积)
/// v2: score = w1×decay + w2×season + w3×affinity + w4×memory + w5×trigger (加权和)
pub fn compute_trigger_score(
    candidate: &ReplayCandidate,
    current_ts: f64,
    current_month: u32,
    user_topic_history: Option<&HashMap<String, u32>>,
    group_memory: Option<&GroupMemoryData>,
) -> f64 {
    let days_since = (current_ts - candidate.last_shown_ts) / 86400.0;

    // 因子 1: 时间衰减
    let decay = if days_since <= 0.0 {
        0.0
    } else {
        1.0 - 0.5_f64.powf(days_since / 30.0)
    };
    let freq_penalty = 1.0 / (1.0 + 0.3 * candidate.show_count as f64);

    // 因子 2: 季节匹配
    let season = get_current_season(current_month);
    let season_score = match candidate.trigger_type {
        ReplayTrigger::Seasonal => seasonal_relevance(&candidate.topics, season),
        _ => 0.5,
    };

    // 因子 3: 用户亲和度
    let affinity = user_topic_history
        .map(|h| compute_user_affinity(h, &candidate.topics))
        .unwrap_or(0.5);

    // 因子 4: 群体记忆信号
    let memory_signal = group_memory
        .map(|gm| {
            if gm.total_reactions == 0 {
                0.5
            } else {
                (gm.resonance_count as f64 / gm.total_reactions as f64 * 1.5).min(1.0)
            }
        })
        .unwrap_or(0.5);

    // 因子 5: 触发类型权重
    let trigger_base = match candidate.trigger_type {
        ReplayTrigger::Seasonal => 0.9,
        ReplayTrigger::Anniversary => 0.7,
        ReplayTrigger::SocialEvent => 0.8,
        ReplayTrigger::ClassicCycle => 0.5,
        ReplayTrigger::GroupMemory => 0.6,
    };

    // 加权和
    0.25 * decay * freq_penalty
        + 0.20 * season_score
        + 0.20 * affinity
        + 0.15 * memory_signal
        + 0.20 * trigger_base
}

/// 时间趋势分析
#[derive(Debug, Clone)]
pub struct TimeTrend {
    pub trend: String,
    pub growth_rate: f64,
    pub latest_intensity: f64,
}

pub fn compute_time_trend(
    reactions_by_period: &HashMap<String, (u32, u32)>,
    // (resonance, opposition)
) -> TimeTrend {
    if reactions_by_period.len() < 2 {
        return TimeTrend {
            trend: "insufficient_data".into(),
            growth_rate: 0.0,
            latest_intensity: 0.0,
        };
    }

    let mut periods: Vec<_> = reactions_by_period.keys().collect();
    periods.sort();

    let counts: Vec<f64> = periods
        .iter()
        .map(|p| reactions_by_period[*p].0 as f64)
        .collect();

    let n = counts.len() as f64;
    let x_mean = (n - 1.0) / 2.0;
    let y_mean = counts.iter().sum::<f64>() / n;

    // 简单线性回归
    let mut num = 0.0;
    let mut den = 0.0;
    for (i, &y) in counts.iter().enumerate() {
        let x = i as f64;
        num += (x - x_mean) * (y - y_mean);
        den += (x - x_mean) * (x - x_mean);
    }
    let slope = if den > 0.0 { num / den } else { 0.0 };

    let avg_count = y_mean;
    let growth_rate = if avg_count > 0.0 { slope / avg_count } else { 0.0 };

    let trend = if growth_rate > 0.1 {
        "growing"
    } else if growth_rate < -0.1 {
        "declining"
    } else {
        "stable"
    };

    let latest = reactions_by_period.get(*periods.last().unwrap()).unwrap();
    let latest_intensity = ((latest.0 + latest.1) as f64 / 50.0).min(1.0);

    TimeTrend {
        trend: trend.into(),
        growth_rate,
        latest_intensity,
    }
}

// ============================================================
// 测试
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_user_affinity_no_history() {
        let history = HashMap::new();
        let topics = vec!["孤独".into()];
        assert_eq!(compute_user_affinity(&history, &topics), 0.5);
    }

    #[test]
    fn test_user_affinity_high_match() {
        let mut history = HashMap::new();
        history.insert("孤独".into(), 8);
        history.insert("音乐".into(), 2);
        let topics = vec!["孤独".into()];
        let aff = compute_user_affinity(&history, &topics);
        assert!(aff > 1.0); // 0.5 + 8/10
    }

    #[test]
    fn test_seasonal_relevance() {
        let topics = vec!["秋天".into(), "落叶".into()];
        assert!(seasonal_relevance(&topics, "autumn") > 0.5);
        assert_eq!(seasonal_relevance(&topics, "spring"), 0.0);
    }

    #[test]
    fn test_trigger_score_basic() {
        let candidate = ReplayCandidate {
            anchor_id: "a1".into(),
            topics: vec!["孤独".into()],
            trigger_type: ReplayTrigger::ClassicCycle,
            last_shown_ts: 0.0,
            show_count: 0,
        };
        let score = compute_trigger_score(&candidate, 1000000.0, 10, None, None);
        assert!(score > 0.0 && score <= 1.0);
    }

    #[test]
    fn test_trigger_score_with_affinity() {
        let candidate = ReplayCandidate {
            anchor_id: "a1".into(),
            topics: vec!["孤独".into()],
            trigger_type: ReplayTrigger::ClassicCycle,
            last_shown_ts: 0.0,
            show_count: 0,
        };
        let mut history = HashMap::new();
        history.insert("孤独".into(), 10);

        let score_no = compute_trigger_score(&candidate, 1000000.0, 10, None, None);
        let score_with = compute_trigger_score(&candidate, 1000000.0, 10, Some(&history), None);
        assert!(score_with > score_no, "有亲和度应更高");
    }

    #[test]
    fn test_time_trend_growing() {
        let mut data = HashMap::new();
        data.insert("Q1".into(), (20, 3));
        data.insert("Q2".into(), (35, 5));
        data.insert("Q3".into(), (48, 4));
        data.insert("Q4".into(), (62, 6));

        let trend = compute_time_trend(&data);
        assert_eq!(trend.trend, "growing");
        assert!(trend.growth_rate > 0.0);
    }

    #[test]
    fn test_time_trend_insufficient() {
        let mut data = HashMap::new();
        data.insert("Q1".into(), (20, 3));
        let trend = compute_time_trend(&data);
        assert_eq!(trend.trend, "insufficient_data");
    }
}
