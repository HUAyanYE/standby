//! 分级响应 v2 — 动态阈值

use standby_shared::types::{ContentReaction, GovernanceLevel, MarkerRecord};

use super::credit::time_decayed_credit;

/// 治理决策结果
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct GovernanceDecision {
    pub level: GovernanceLevel,
    pub harmful_weight: f64,
    pub marker_avg_credit: f64,
    pub reason: String,
    pub actions: Vec<String>,
}

/// 动态阈值计算
///
/// 争议性话题自动提高阈值, 热门内容适当提高阈值
pub fn compute_dynamic_threshold(
    base: f64,
    controversy: f64,
    heat: usize,
) -> f64 {
    let controversy_factor = 1.0 + 0.5 * controversy;
    let heat_factor = 1.0 + 0.3 * (heat as f64 / 200.0).min(1.0);
    base * controversy_factor * heat_factor
}

/// 分级响应评估 v2
pub fn evaluate_governance(
    reactions: &ContentReaction,
    marker_credits: &[f64],
    base_threshold: f64,
    min_samples: u32,
    current_ts: f64,
) -> GovernanceDecision {
    let total = reactions.total();
    let harmful_r = reactions.harmful_ratio();
    let resonance_r = reactions.resonance_ratio();

    // 时间衰减信用 (v2)
    let avg_credit = if marker_credits.is_empty() {
        0.5
    } else {
        let decayed: f64 = marker_credits
            .iter()
            .map(|&c| {
                let m = MarkerRecord {
                    token_hash: String::new(),
                    credit_score: c,
                    total_marks: 10,
                    accurate_marks: (c * 10.0) as u32,
                    last_mark_ts: current_ts - 86400.0 * 60.0,
                };
                time_decayed_credit(&m, current_ts, 90.0)
            })
            .sum();
        decayed / marker_credits.len() as f64
    };

    // 有害加权
    let harmful_weight = avg_credit * reactions.harmful as f64;

    // 样本不足
    if total < min_samples {
        return GovernanceDecision {
            level: GovernanceLevel::Normal,
            harmful_weight,
            marker_avg_credit: avg_credit,
            reason: format!("样本不足 ({total} < {min_samples})"),
            actions: vec![],
        };
    }

    // 动态阈值
    let controversy = 1.0 - (resonance_r - 0.5).abs() * 2.0;
    let dynamic_threshold = compute_dynamic_threshold(base_threshold, controversy, total as usize);

    // 共鸣/有害冲突
    if harmful_r > base_threshold && resonance_r > 0.3 {
        if avg_credit < 0.3 {
            return GovernanceDecision {
                level: GovernanceLevel::Observing,
                harmful_weight,
                marker_avg_credit: avg_credit,
                reason: format!("有害标记者信用低({:.2}), 可能是恶意刷标", avg_credit),
                actions: vec!["记录观察".into(), "降低该批标记权重".into()],
            };
        }
        return GovernanceDecision {
            level: GovernanceLevel::Conflict,
            harmful_weight,
            marker_avg_credit: avg_credit,
            reason: format!("共鸣/有害冲突 (有害{:.0}%, 共鸣{:.0}%)", harmful_r * 100.0, resonance_r * 100.0),
            actions: vec!["标记为争议".into(), "共鸣权重×0.5".into(), "展示正反双方观点".into()],
        };
    }

    // 分级响应
    if harmful_r >= dynamic_threshold * 2.5 && avg_credit > 0.4 {
        GovernanceDecision {
            level: GovernanceLevel::Removed,
            harmful_weight,
            marker_avg_credit: avg_credit,
            reason: format!("有害标记严重 ({:.0}%)", harmful_r * 100.0),
            actions: vec!["停止展示".into(), "通知作者".into(), "提供申诉入口".into()],
        }
    } else if harmful_r >= dynamic_threshold * 1.5 && avg_credit > 0.4 {
        GovernanceDecision {
            level: GovernanceLevel::Suspended,
            harmful_weight,
            marker_avg_credit: avg_credit,
            reason: format!("有害标记显著 ({:.0}%)", harmful_r * 100.0),
            actions: vec!["暂停展示".into(), "进入复核队列".into()],
        }
    } else if harmful_r >= dynamic_threshold && avg_credit > 0.4 {
        GovernanceDecision {
            level: GovernanceLevel::Demoted,
            harmful_weight,
            marker_avg_credit: avg_credit,
            reason: format!("有害标记达到阈值 ({:.0}%)", harmful_r * 100.0),
            actions: vec!["降低展示优先级".into()],
        }
    } else if harmful_r > 0.0 {
        GovernanceDecision {
            level: GovernanceLevel::Observing,
            harmful_weight,
            marker_avg_credit: avg_credit,
            reason: format!("少量有害标记 ({:.0}%), 记录观察", harmful_r * 100.0),
            actions: vec![],
        }
    } else {
        GovernanceDecision {
            level: GovernanceLevel::Normal,
            harmful_weight,
            marker_avg_credit: avg_credit,
            reason: "无异常信号".into(),
            actions: vec![],
        }
    }
}

// ============================================================
// 测试
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_normal_content() {
        let r = ContentReaction {
            anchor_id: "a1".into(),
            resonance: 50,
            neutral: 20,
            opposition: 10,
            unexperienced: 5,
            harmful: 0, // 无有害标记 → Normal
        };
        let d = evaluate_governance(&r, &[0.5; 0], 0.15, 10, 0.0);
        assert_eq!(d.level, GovernanceLevel::Normal);
    }

    #[test]
    fn test_conflict() {
        let r = ContentReaction {
            anchor_id: "a1".into(),
            resonance: 40,
            neutral: 10,
            opposition: 10,
            unexperienced: 5,
            harmful: 20, // 29% 有害, 57% 共鸣
        };
        let d = evaluate_governance(&r, &[0.5; 20], 0.15, 10, 0.0);
        assert_eq!(d.level, GovernanceLevel::Conflict);
    }

    #[test]
    fn test_removed() {
        let r = ContentReaction {
            anchor_id: "a1".into(),
            resonance: 10,
            neutral: 5,
            opposition: 5,
            unexperienced: 0,
            harmful: 50, // 71% 有害
        };
        let d = evaluate_governance(&r, &[0.5; 50], 0.15, 10, 0.0);
        assert_eq!(d.level, GovernanceLevel::Removed);
    }

    #[test]
    fn test_dynamic_threshold() {
        // 普通内容 (heat=0 → heat_factor=1.0)
        let t1 = compute_dynamic_threshold(0.15, 0.0, 0);
        assert!((t1 - 0.15).abs() < 0.001);

        // 争议话题
        let t2 = compute_dynamic_threshold(0.15, 0.8, 0);
        assert!(t2 > t1);

        // 热门内容
        let t3 = compute_dynamic_threshold(0.15, 0.0, 500);
        assert!(t3 > t1);
    }

    #[test]
    fn test_insufficient_samples() {
        let r = ContentReaction {
            anchor_id: "a1".into(),
            resonance: 2,
            neutral: 1,
            opposition: 0,
            unexperienced: 0,
            harmful: 1,
        };
        let d = evaluate_governance(&r, &[0.5], 0.15, 10, 0.0);
        assert_eq!(d.level, GovernanceLevel::Normal);
        assert!(d.reason.contains("样本不足"));
    }
}
