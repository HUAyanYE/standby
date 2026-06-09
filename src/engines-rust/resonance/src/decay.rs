//! 话题衰减 & 跨话题加权 v2

use std::collections::HashMap;

/// 话题内衰减 (v1 保持, 双曲线方案经验证合理)
///
/// decay = 1 / (1 + α × (n - 1))
pub fn topic_decay(n_topic: usize, alpha: f64) -> f64 {
    1.0 / (1.0 + alpha * (n_topic.saturating_sub(1)) as f64)
}

/// 跨话题加权 v2: Shannon 熵替代简单计数
///
/// v1: bonus = β × ln(unique_topics + 1)
/// v2: bonus = β × normalized_shannon_entropy(topic_distribution)
pub fn diversity_bonus(topic_counts: &HashMap<String, usize>, beta: f64) -> f64 {
    let total: usize = topic_counts.values().sum();
    if total <= 1 {
        return 0.0;
    }

    // Shannon 熵
    let mut entropy = 0.0_f64;
    for &count in topic_counts.values() {
        if count > 0 {
            let p = count as f64 / total as f64;
            entropy -= p * p.ln();
        }
    }

    // 归一化
    let n_topics = topic_counts.len();
    if n_topics <= 1 {
        return 0.0;
    }
    let max_entropy = (n_topics as f64).ln();
    let normalized = entropy / max_entropy;

    beta * normalized
}

/// 关系分记录
#[derive(Debug, Clone)]
pub struct ResonanceRecord {
    pub value: f64,
    pub topic: String,
    pub timestamp: f64,
}

/// 关系分结果
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct RelationshipScore {
    pub score: f64,
    pub unique_topics: usize,
    pub resonance_count: usize,
}

/// 关系分聚合 v2 (含时间加权)
pub fn compute_relationship_score(
    records: &[ResonanceRecord],
    time_weight_half_life: f64,
    current_ts: f64,
) -> RelationshipScore {
    if records.is_empty() {
        return RelationshipScore {
            score: 0.0,
            unique_topics: 0,
            resonance_count: 0,
        };
    }

    let mut topic_counts: HashMap<String, usize> = HashMap::new();
    let mut active_score = 0.0_f64;

    for record in records {
        *topic_counts.entry(record.topic.clone()).or_insert(0) += 1;
        let n = topic_counts[&record.topic];
        let decay = topic_decay(n, 0.3);

        // 时间加权
        let days_ago = (current_ts - record.timestamp) / 86400.0;
        let time_weight = if days_ago > 0.0 {
            0.5_f64.powf(days_ago / time_weight_half_life)
        } else {
            1.0
        };

        active_score += record.value * decay * time_weight;
    }

    let bonus = diversity_bonus(&topic_counts, 0.15);
    let final_score = active_score * (1.0 + bonus);

    RelationshipScore {
        score: final_score,
        unique_topics: topic_counts.len(),
        resonance_count: records.len(),
    }
}

// ============================================================
// 测试
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_topic_decay_first() {
        assert!((topic_decay(1, 0.3) - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_topic_decay_monotonic() {
        for n in 1..20 {
            assert!(topic_decay(n, 0.3) <= topic_decay(n - 1, 0.3));
        }
    }

    #[test]
    fn test_topic_decay_values() {
        // α=0.3 时: n=1→1.0, n=2→0.769, n=5→0.455, n=10→0.270
        assert!((topic_decay(1, 0.3) - 1.00).abs() < 0.01);
        assert!((topic_decay(2, 0.3) - 0.769).abs() < 0.01);
        assert!((topic_decay(5, 0.3) - 0.455).abs() < 0.01);
        assert!((topic_decay(10, 0.3) - 0.270).abs() < 0.01);
    }

    #[test]
    fn test_diversity_single_topic() {
        let mut counts = HashMap::new();
        counts.insert("孤独".into(), 5);
        assert_eq!(diversity_bonus(&counts, 0.15), 0.0);
    }

    #[test]
    fn test_diversity_uniform_higher() {
        let mut counts1 = HashMap::new();
        counts1.insert("孤独".into(), 5);
        counts1.insert("音乐".into(), 5);

        let mut counts2 = HashMap::new();
        counts2.insert("孤独".into(), 9);
        counts2.insert("音乐".into(), 1);

        // 均匀分布 → 熵更高
        assert!(diversity_bonus(&counts1, 0.15) > diversity_bonus(&counts2, 0.15));
    }

    #[test]
    fn test_relationship_empty() {
        let result = compute_relationship_score(&[], 180.0, 0.0);
        assert_eq!(result.score, 0.0);
    }

    #[test]
    fn test_relationship_same_topic_decay() {
        let records = vec![
            ResonanceRecord {
                value: 0.8,
                topic: "孤独".into(),
                timestamp: 0.0,
            },
            ResonanceRecord {
                value: 0.8,
                topic: "孤独".into(),
                timestamp: 0.0,
            },
            ResonanceRecord {
                value: 0.8,
                topic: "孤独".into(),
                timestamp: 0.0,
            },
        ];
        let result = compute_relationship_score(&records, 180.0, 0.0);

        // 同话题衰减:
        // n=1: decay=1.0, contrib=0.8*1.0=0.8
        // n=2: decay=0.769, contrib=0.8*0.769=0.615
        // n=3: decay=0.625, contrib=0.8*0.625=0.5
        // total = 0.8+0.615+0.5 = 1.915
        // 无多样性加成 (单话题, bonus=0)
        assert!((result.score - 1.915).abs() < 0.01, "score={}", result.score);
    }

    #[test]
    fn test_relationship_time_decay() {
        let now = 1000000.0;
        let records = vec![
            ResonanceRecord { value: 1.0, topic: "孤独".into(), timestamp: now },
            ResonanceRecord { value: 1.0, topic: "孤独".into(), timestamp: now - 180.0 * 86400.0 },
        ];
        let result = compute_relationship_score(&records, 180.0, now);

        // 第二条半年前, 时间权重 = 0.5
        // 第一条: 1.0*1.0*1.0 = 1.0
        // 第二条: 1.0*0.77*0.5 = 0.385
        // 总 ≈ 1.385
        assert!(result.score > 1.0 && result.score < 2.0);
    }
}
