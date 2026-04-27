//! Standby 内容治理引擎 v2 (Rust 生产版)
//!
//! 对齐 Python rule_governance_v2.py 的全部算法:
//! 1. Bayesian Beta 后验标记者信用
//! 2. 时间衰减信用
//! 3. 动态阈值
//! 4. 话题类型打击检测
//! 5. 速度异常检测
//! 6. 协同攻击检测 (v2)
//! 7. 分级响应 (v2)

pub mod credit;
pub mod detection;
pub mod evaluate;

pub use credit::*;
pub use detection::*;
pub use evaluate::*;
