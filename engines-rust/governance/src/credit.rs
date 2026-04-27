//! 标记者信用 v2 — Bayesian + 时间衰减

use standby_shared::types::MarkerRecord;

/// Bayesian Beta 后验更新标记者信用
///
/// v1: credit = accuracy × volume_weight
/// v2: posterior_mean = (α_prior + accurate) / (α_prior + β_prior + total)
pub fn update_marker_credit_bayesian(
    marker: &mut MarkerRecord,
    was_accurate: bool,
    prior_alpha: f64,
    prior_beta: f64,
    current_ts: f64,
) {
    marker.total_marks += 1;
    if was_accurate {
        marker.accurate_marks += 1;
    }

    // Bayesian 后验
    let alpha = prior_alpha + marker.accurate_marks as f64;
    let beta = prior_beta + (marker.total_marks - marker.accurate_marks) as f64;
    let posterior_mean = alpha / (alpha + beta);

    // 标记量异常惩罚
    let volume_penalty = if marker.total_marks > 200 {
        0.7
    } else if marker.total_marks < 5 {
        0.8
    } else {
        1.0
    };

    marker.credit_score = (posterior_mean * volume_penalty).clamp(0.0, 1.0);
    marker.last_mark_ts = current_ts;
}

/// 时间衰减信用
///
/// 30 天内活跃 → 不衰减
/// 超过 30 天 → 向先验值 0.5 指数衰减
pub fn time_decayed_credit(marker: &MarkerRecord, current_ts: f64, half_life_days: f64) -> f64 {
    if marker.last_mark_ts <= 0.0 {
        return marker.credit_score;
    }

    let days_inactive = (current_ts - marker.last_mark_ts) / 86400.0;
    if days_inactive <= 30.0 {
        return marker.credit_score;
    }

    let decay_factor = 0.5_f64.powf((days_inactive - 30.0) / half_life_days);
    let decayed = 0.5 + (marker.credit_score - 0.5) * decay_factor;
    decayed.clamp(0.5, 1.0)
}

// ============================================================
// 测试
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bayesian_new_user() {
        let mut m = MarkerRecord::new("test".into());
        update_marker_credit_bayesian(&mut m, true, 2.0, 2.0, 0.0);

        // 先验 Beta(2,2), 1次准确 → Beta(3,2) → 3/5 = 0.6
        // volume_penalty = 0.8 (<5次) → 0.48
        assert!((m.credit_score - 0.48).abs() < 0.01);
        assert_eq!(m.total_marks, 1);
        assert_eq!(m.accurate_marks, 1);
    }

    #[test]
    fn test_bayesian_established_user() {
        let mut m = MarkerRecord::new("test".into());
        for _ in 0..10 {
            update_marker_credit_bayesian(&mut m, true, 2.0, 2.0, 0.0);
        }
        // 10次全准确 → Beta(12,2) → 12/14 ≈ 0.857
        assert!(m.credit_score > 0.8);
    }

    #[test]
    fn test_bayesian_mixed() {
        let mut m = MarkerRecord::new("test".into());
        for _ in 0..5 {
            update_marker_credit_bayesian(&mut m, true, 2.0, 2.0, 0.0);
        }
        for _ in 0..5 {
            update_marker_credit_bayesian(&mut m, false, 2.0, 2.0, 0.0);
        }
        // 5准5误 → Beta(7,7) → 7/14 = 0.5
        assert!((m.credit_score - 0.5).abs() < 0.05);
    }

    #[test]
    fn test_time_decay_active_user() {
        let m = MarkerRecord {
            token_hash: "t".into(),
            credit_score: 0.8,
            total_marks: 20,
            accurate_marks: 16,
            last_mark_ts: 1000000.0,
        };
        let decayed = time_decayed_credit(&m, 1000000.0 + 86400.0 * 10.0, 90.0);
        assert!((decayed - 0.8).abs() < 0.001, "活跃用户不衰减");
    }

    #[test]
    fn test_time_decay_idle_user() {
        let m = MarkerRecord {
            token_hash: "t".into(),
            credit_score: 0.8,
            total_marks: 20,
            accurate_marks: 16,
            last_mark_ts: 1000000.0,
        };
        let decayed = time_decayed_credit(&m, 1000000.0 + 86400.0 * 180.0, 90.0);
        assert!(decayed < 0.8, "闲置用户应衰减");
        assert!(decayed >= 0.5, "不低于先验值");
    }
}
