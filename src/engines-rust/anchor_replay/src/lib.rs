//! Standby 锚点重现引擎 v2 (Rust 生产版)
//!
//! 对齐 Python anchor_replay_v2.py 的全部算法:
//! 1. 多因子触发评分 (加权和替代乘积)
//! 2. 用户亲和度
//! 3. 群体记忆时间趋势
//! 4. Shannon 熵跨话题加权 (复用 resonance crate)

pub mod replay;

pub use replay::*;
