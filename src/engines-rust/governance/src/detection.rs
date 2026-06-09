//! 异常检测 v2

/// 速度异常检测
///
/// 滑动窗口内反应数超过阈值 → 机器人/脚本
pub fn detect_velocity_anomaly(
    timestamps: &[f64],
    window_seconds: f64,
    max_reactions: usize,
) -> (bool, String) {
    if timestamps.len() < max_reactions {
        return (false, "正常".into());
    }

    let mut sorted: Vec<f64> = timestamps.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());

    for window in sorted.windows(max_reactions) {
        let span = window[max_reactions - 1] - window[0];
        if span <= window_seconds {
            return (true, format!("速度异常: {max_reactions}次/{span:.0}秒内"));
        }
    }

    (false, "正常".into())
}

/// 协同攻击检测 v2
///
/// v2: 同时检测来源聚集度
pub fn detect_coordinated_marking(
    timestamps: &[f64],
    marker_ids: &[String],
    time_window_seconds: f64,
    threshold: usize,
) -> (bool, String) {
    if timestamps.len() < threshold {
        return (false, "正常".into());
    }

    // 按时间排序
    let mut pairs: Vec<(f64, &String)> = timestamps
        .iter()
        .copied()
        .zip(marker_ids.iter())
        .collect();
    pairs.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());

    for window in pairs.windows(threshold) {
        let time_span = window[threshold - 1].0 - window[0].0;
        if time_span <= time_window_seconds {
            let unique_markers: std::collections::HashSet<_> =
                window.iter().map(|(_, id)| id).collect();
            let concentration = unique_markers.len() as f64 / threshold as f64;

            if concentration < 0.3 {
                return (
                    true,
                    format!(
                        "协同攻击: {threshold}次/{time_span:.0}秒, 仅{}个独立来源",
                        unique_markers.len()
                    ),
                );
            }
        }
    }

    (false, "正常".into())
}

/// 话题类型打击检测 v2 (v1 未实现)
///
/// 检测某类反应被系统性标记为未体验
pub fn detect_topic_type_attack(
    type_unexperienced_counts: &std::collections::HashMap<String, (u32, u32)>,
    // (total, unexperienced)
    unexperienced_threshold: f64,
    min_samples: u32,
) -> (bool, String) {
    let total: u32 = type_unexperienced_counts.values().map(|(t, _)| t).sum();
    if total < min_samples {
        return (false, "样本不足".into());
    }

    let total_unexp: u32 = type_unexperienced_counts.values().map(|(_, u)| u).sum();
    let overall_rate = total_unexp as f64 / total as f64;

    let mut anomalies = Vec::new();
    for (rtype, &(type_total, type_unexp)) in type_unexperienced_counts {
        if type_total < 5 {
            continue;
        }
        let type_rate = type_unexp as f64 / type_total as f64;
        if type_rate > unexperienced_threshold && type_rate > overall_rate * 2.0 {
            anomalies.push(format!(
                "{rtype}: {:.0}% (整体{:.0}%)",
                type_rate * 100.0,
                overall_rate * 100.0
            ));
        }
    }

    if anomalies.is_empty() {
        (false, "正常".into())
    } else {
        (true, format!("类型打击检测: {}", anomalies.join("; ")))
    }
}

// ============================================================
// 测试
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    #[test]
    fn test_velocity_normal() {
        let ts: Vec<f64> = (0..15).map(|i| 1000.0 + i as f64 * 3600.0).collect();
        let (anomaly, _) = detect_velocity_anomaly(&ts, 60.0, 10);
        assert!(!anomaly);
    }

    #[test]
    fn test_velocity_bot() {
        let ts: Vec<f64> = (0..15).map(|i| 1000.0 + i as f64 * 3.0).collect();
        let (anomaly, reason) = detect_velocity_anomaly(&ts, 60.0, 10);
        assert!(anomaly);
        assert!(reason.contains("速度异常"));
    }

    #[test]
    fn test_coordinated_attack() {
        let ts: Vec<f64> = (0..15).map(|i| 1000.0 + i as f64 * 10.0).collect();
        let ids: Vec<String> = vec!["m1".into(); 15];
        let (anomaly, reason) = detect_coordinated_marking(&ts, &ids, 300.0, 10);
        assert!(anomaly);
        assert!(reason.contains("协同攻击"));
    }

    #[test]
    fn test_coordinated_normal() {
        let ts: Vec<f64> = (0..15).map(|i| 1000.0 + i as f64 * 3600.0).collect();
        let ids: Vec<String> = (0..15).map(|i| format!("m{i}")).collect();
        let (anomaly, _) = detect_coordinated_marking(&ts, &ids, 300.0, 10);
        assert!(!anomaly);
    }

    #[test]
    fn test_type_attack_detected() {
        let mut data = HashMap::new();
        data.insert("共鸣".into(), (40, 1));
        data.insert("反对".into(), (7, 5)); // 71% 未体验

        let (anomaly, reason) = detect_topic_type_attack(&data, 0.4, 10);
        assert!(anomaly);
        assert!(reason.contains("反对"));
    }

    #[test]
    fn test_type_attack_normal() {
        let mut data = HashMap::new();
        data.insert("共鸣".into(), (40, 2));
        data.insert("反对".into(), (15, 1));

        let (anomaly, _) = detect_topic_type_attack(&data, 0.4, 10);
        assert!(!anomaly);
    }
}
