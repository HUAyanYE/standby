//! Standby 共鸣机制引擎 v2 (Rust 生产版)
//!
//! 对齐 Python resonance_calculator_v2.py 的全部算法:
//! 1. Sigmoid 相关性过滤 (替代硬阈值)
//! 2. 聚类感知 Novelty (k-NN 均值 + 密度衰减)
//! 3. 复合深度信号 (字数 × 语义正交性)
//! 4. 对齐 PRD 的 4 个情绪词
//! 5. 指数型惩罚函数
//! 6. Shannon 熵跨话题加权
//! 7. 时间加权关系分聚合

pub mod resonance;
pub mod penalty;
pub mod decay;

pub use resonance::*;
pub use penalty::*;
pub use decay::*;
