//! 惩罚函数 v2 — 指数型替代线性

/// 指数型有害惩罚
///
/// v1: max(0, 1.0 - ratio * 2) — 线性
/// v2: exp(-3 * ratio) — 指数衰减
///
/// - ratio=0.1 → 0.74 (温和)
/// - ratio=0.3 → 0.41 (严厉)
/// - ratio=0.5 → 0.22 (几乎归零)
pub fn harmful_penalty(ratio: f64) -> f64 {
    (-3.0 * ratio).exp()
}

/// 指数型未体验惩罚 (比有害温和)
pub fn unexperienced_penalty(ratio: f64) -> f64 {
    (-2.0 * ratio).exp()
}

// ============================================================
// 测试
// ============================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_harmful_no_harm() {
        assert!((harmful_penalty(0.0) - 1.0).abs() < 0.001);
    }

    #[test]
    fn test_harmful_low() {
        let p = harmful_penalty(0.1);
        assert!((p - 0.7408).abs() < 0.01);
    }

    #[test]
    fn test_harmful_medium() {
        let p = harmful_penalty(0.3);
        assert!((p - 0.4066).abs() < 0.01);
    }

    #[test]
    fn test_harmful_high() {
        let p = harmful_penalty(0.5);
        assert!((p - 0.2231).abs() < 0.01);
    }

    #[test]
    fn test_unexperienced_always_milder() {
        for ratio in [0.1, 0.2, 0.3, 0.5] {
            assert!(
                unexperienced_penalty(ratio) > harmful_penalty(ratio),
                "未体验惩罚应比有害更温和 (ratio={ratio})"
            );
        }
    }

    #[test]
    fn test_penalty_monotonic() {
        for i in 0..100 {
            let r1 = i as f64 / 100.0;
            let r2 = (i + 1) as f64 / 100.0;
            assert!(harmful_penalty(r1) >= harmful_penalty(r2));
            assert!(unexperienced_penalty(r1) >= unexperienced_penalty(r2));
        }
    }
}
